# -*- coding: utf-8 -*-
"""网络环境模拟工具（弱网 / 断网专项测试用）。

设计背景：
真实项目的弱网测试通常用 Charles / Fiddler 做限速、丢包、高延迟；
Android 模拟器还可用 Appium 的 `mobile: setConnectivity` 切换网络类型，
或用 `adb shell settings put global airplane_mode_on 1` 进飞行模式。

本机实测结论（写在这里，避免重复踩坑）：
- `driver.set_network_speed()` **在雷电模拟器上不可用**（它依赖 AVD 的 `-netspeed` 参数，
  报 Error executing adbExec）。
- `driver.set_network_connection(value)` 内部会执行 `adb shell svc data disable`，
  在雷电上会把进程杀掉（exit 137 / call killProcess）。
- `adb shell svc wifi disable` 同样导致设备 offline。
- `adb shell settings put global airplane_mode_on 1` 能进飞行模式，但也会让 adb 一并断开
  （雷电的 adb 走 host 网络），设备 offline 后无法远程恢复，只能重启模拟器。

**根本原因**：雷电模拟器的 adb 通过 host 网络端口连接（而非本地管道），
所以任何「关闭设备网络」的操作都会把 adb 连接本身一起断掉。
AVD（Android Virtual Device）用本地管道，不受此影响 —— 这就是
`set_network_speed` / 网络切换在 AVD 上正常、在雷电上不可用的原因。

因此这里提供两层能力：
1. `probe()`：先探测当前环境是否支持网络切换（不断连接的方式），
   不支持就返回 False，让用例可以 skip 而不是失败。
2. `set_connectivity()`：在支持的环境（AVD / 真机）上切换网络类型。
"""
from __future__ import annotations

import subprocess

# network_connection 位掩码
AIRPLANE_MODE = 1
WIFI_ONLY = 2
DATA_ONLY = 4
ALL_ON = 6  # WiFi + 数据

#: 探测时的 adb 命令超时（秒）
_ADB_TIMEOUT = 12


def _find_adb() -> str:
    import os

    for candidate in (
        os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb"),
        os.path.join(os.environ.get("ANDROID_SDK_ROOT", ""), "platform-tools", "adb"),
        "adb",
    ):
        if candidate == "adb" or os.path.isfile(candidate) or os.path.isfile(candidate + ".exe"):
            return candidate
    return "adb"


class NetworkCondition:
    """网络环境模拟器。

    用法::

        net = NetworkCondition(driver)
        if not net.probe():
            pytest.skip("当前环境不支持网络切换模拟")

        net.set_connectivity(NetworkCondition.WIFI_ONLY)
        ... 执行被测操作 ...
        net.restore()
    """

    def __init__(self, driver):
        self.driver = driver
        self._supported: bool | None = None

    # ---------------------------------------------------------------- 能力探测

    def probe(self, device_udid: str | None = None) -> bool:
        """探测当前设备是否支持「不断 adb」的网络切换。

        做法：**真的做一次最小切换再切回**，然后确认 adb 仍然在线。
        只跑只读命令是不够的 —— 雷电上 `dumpsys connectivity` 能正常返回 0，
        但 `svc data disable` 会杀进程。所以必须实测一次写操作。

        返回 True 表示「本环境可安全做网络切换实验」。
        """
        if self._supported is not None:
            return self._supported

        try:
            before = self.current
        except Exception:
            self._supported = False
            return False

        # 尝试一次「切换到仅 WiFi 再切回」的最小实验
        try:
            self.set_connectivity(WIFI_ONLY)
            switched = self.current
            self.set_connectivity(before if before else ALL_ON)
            after = self.current
            ok = True
        except Exception:
            ok = False
            switched = after = None

        # 关键：切换后 adb 必须还能通信，否则说明环境会断连
        if ok:
            ok = self._adb_still_alive(device_udid)

        self._supported = ok
        return ok

    def _adb_still_alive(self, device_udid: str | None = None) -> bool:
        """确认 adb 与设备仍然连通。"""
        udid = device_udid or getattr(self.driver, "capabilities", {}).get("deviceUDID")
        adb = _find_adb()
        cmd = [adb] + (["-s", udid] if udid else []) + ["shell", "echo", "probe-ok"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  errors="replace", timeout=_ADB_TIMEOUT)
            return proc.returncode == 0 and "probe-ok" in (proc.stdout or "")
        except Exception:
            return False

    # ---------------------------------------------------------------- 读状态

    @property
    def current(self) -> int:
        """当前网络连接位掩码。"""
        return int(self.driver.network_connection)

    # ---------------------------------------------------------------- 切网

    def set_connectivity(self, value: int) -> int:
        """设置网络连接，返回设置后的实际值。

        注意：必须用 `set_network_connection()` 方法；该 Python 客户端的
        `network_connection` 属性只有 getter，直接赋值会报 has no setter。
        """
        self.driver.set_network_connection(value)
        return self.current

    def go_wifi_only(self) -> int:
        """仅保留 WiFi（断开移动数据）。"""
        return self.set_connectivity(WIFI_ONLY)

    def go_data_only(self) -> int:
        """仅保留移动数据。"""
        return self.set_connectivity(DATA_ONLY)

    def go_airplane(self) -> int:
        """飞行模式。

        ⚠️ 在雷电模拟器上会导致 adb 断开且无法远程恢复（只能重启模拟器），
        仅建议在 AVD 或真机上使用。
        """
        return self.set_connectivity(AIRPLANE_MODE)

    def restore(self) -> int:
        """恢复正常网络（WiFi + 数据）。"""
        return self.set_connectivity(ALL_ON)
