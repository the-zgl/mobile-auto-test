# -*- coding: utf-8 -*-
"""探测 Appium 网络模拟能力在当前设备上是否可用（不写业务逻辑，只做能力验证）。"""
import sys

from appium import webdriver
from appium.options.android import UiAutomator2Options

CAPS = {
    "platformName": "Android",
    "platformVersion": "9",
    "deviceName": "emulator-5560",
    "automationName": "UiAutomator2",
    "appPackage": "com.daping.demoshop",
    "appActivity": ".LoginActivity",
    "noReset": True,
}


def main():
    opts = UiAutomator2Options()
    for k, v in CAPS.items():
        setattr(opts, k, v)
    opts.udid = CAPS["deviceName"]

    drv = webdriver.Remote("http://127.0.0.1:4723", options=opts)
    try:
        print("会话已建立")

        # 1) 读取当前网络连接类型
        try:
            conn = drv.network_connection
            print(f"当前 network_connection = {conn} (1=airplane, 2=wifi only, 4=data only, 6=all)")
        except Exception as exc:
            print(f"network_connection 读取失败: {exc}")

        # 2) 尝试设置网络速度（Android Emulator 特性）
        for speed in ("gsm", "edge", "lte"):
            try:
                drv.set_network_speed(speed)
                print(f"set_network_speed({speed}) 成功")
            except Exception as exc:
                msg = str(exc).replace("\n", " ")[:150]
                print(f"set_network_speed({speed}) 失败: {msg}")
                break
    finally:
        drv.quit()


if __name__ == "__main__":
    sys.exit(main())
