# -*- coding: utf-8 -*-
"""实测 network_connection 的可用取值（弱网/断网模拟的可用手段）。"""
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
        # network_connection 位掩码：1=飞行模式 2=WiFi 4=数据
        # 常见组合：1(airplane) 2(wifi only) 4(data only) 6(wifi+data)
        # 注意：必须用 set_network_connection() 方法；该 Python 客户端的
        # network_connection 属性只有 getter，直接赋值会报 has no setter。
        for value, label in [(6, "WiFi+数据（正常）"), (2, "仅 WiFi"), (4, "仅数据"),
                             (1, "飞行模式")]:
            try:
                drv.set_network_connection(value)
                now = drv.network_connection
                print(f"设置 {value}（{label}）-> 实际生效 {now}")
            except Exception as exc:
                print(f"设置 {value}（{label}）失败: {str(exc)[:120]}")

        # 恢复
        drv.set_network_connection(6)
        print(f"已恢复为 6，当前 {drv.network_connection}")
    finally:
        drv.quit()


if __name__ == "__main__":
    sys.exit(main())
