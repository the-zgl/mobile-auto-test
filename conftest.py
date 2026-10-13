# -*- coding: utf-8 -*-
"""pytest 公共 fixture：读取配置 + 创建/销毁 Appium driver + 用例间状态隔离。

设计要点：
1. driver 用 function 作用域：每条用例一个干净的 App 会话；
2. **每条用例前清空 App 数据**（pm clear）：被测 App 把余额存在 SharedPreferences 里，
   不清数据的话「上一条用例花掉的钱」会污染下一条用例的断言；
3. 连接失败时报错信息里直接给出排查清单，减少「跑不起来」的沟通成本；
4. `--no-device` 时自动跳过真实用例，只保留配置校验，方便在没有模拟器的机器上做冒烟。
"""
import os
import subprocess

import pytest
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "config.yaml")

#: 从 Appium 会话能力里取包名用不上，这里直接用 adb 清数据，
#: 所以需要知道 adb 在哪：优先环境变量，其次 PATH。
ADB_CANDIDATES = [
    os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb"),
    os.path.join(os.environ.get("ANDROID_SDK_ROOT", ""), "platform-tools", "adb"),
    "adb",
]


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def pytest_addoption(parser):
    parser.addoption(
        "--no-device",
        action="store_true",
        default=False,
        help="不连接真机/模拟器（只用例收集与配置校验，CI 里用）",
    )
    parser.addoption(
        "--keep-app-data",
        action="store_true",
        default=False,
        help="用例之间不清空 App 数据（默认会清，保证隔离）",
    )


def find_adb():
    """定位 adb 可执行文件，找不到就返回 None。"""
    for candidate in ADB_CANDIDATES:
        if not candidate:
            continue
        if candidate == "adb":
            return candidate  # 交给 PATH 去找
        if os.path.isfile(candidate) or os.path.isfile(candidate + ".exe"):
            return candidate
    return "adb"


def clear_app_data(device_name, app_package):
    """清空被测 App 的数据（相当于「设置 → 应用 → 清除数据」）。

    这样每条用例都从「首次安装后」的状态开始：
    余额回到初始值、上一轮的支付成功提示也不会残留。
    """
    adb = find_adb()
    result = subprocess.run(
        [adb, "-s", device_name, "shell", "pm", "clear", app_package],
        capture_output=True,
        text=True,
        errors="replace",
    )
    return result.returncode == 0 and "Success" in (result.stdout or "")


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture(scope="session")
def caps(config):
    return config["caps"]


@pytest.fixture(scope="function")
def driver(request, config, caps):
    """按配置创建 Appium 会话；用例结束后退出，保证隔离。"""
    if request.config.getoption("--no-device"):
        pytest.skip("--no-device：跳过需要真实设备的用例")

    from appium import webdriver
    from appium.options.android import UiAutomator2Options

    # ---- 用例开始前先清数据，保证初始状态可预期 ----
    if not request.config.getoption("--keep-app-data"):
        if not clear_app_data(caps.get("deviceName"), caps.get("appPackage")):
            pytest.fail(
                f"清空 {caps.get('appPackage')} 数据失败。请确认：\n"
                f"  1) adb 可用（在 PATH 里，或设好 ANDROID_HOME）；\n"
                f"  2) 设备 {caps.get('deviceName')} 在线（adb devices）。\n"
                "若确实不想清数据，可加 --keep-app-data 参数。"
            )

    options = UiAutomator2Options()
    options.platform_name = caps["platformName"]
    options.platform_version = caps.get("platformVersion")
    options.device_name = caps.get("deviceName")
    # 关键：同时连了多台设备（雷电多开）时，Appium 会忽略 deviceName 而自己挑一台，
    # 结果连到没装被测 App 的那台上。用 udid 显式锁定设备，避免"连错机"这类假失败。
    options.udid = caps.get("deviceName")
    options.automation_name = caps.get("automationName", "UiAutomator2")
    options.app_package = caps.get("appPackage")
    options.app_activity = caps.get("appActivity")
    options.no_reset = caps.get("noReset", True)

    url = config["appium"]["url"]
    try:
        drv = webdriver.Remote(url, options=options)
    except Exception as exc:  # noqa: BLE001 - 需要把排查清单给到使用者
        pytest.fail(
            f"无法连接 Appium 服务 {url}：{exc}\n"
            "排查清单：\n"
            "  1) Appium Server 是否已启动（appium 命令）？\n"
            "  2) 模拟器/真机是否已连接（adb devices 能看到设备）？\n"
            "  3) config/config.yaml 里的 deviceName / platformVersion 是否匹配？\n"
            "  4) 被测 App 是否已安装（adb install -r app-debug.apk）？\n"
            "  5) Appium 服务进程是否带上了 ANDROID_HOME（否则会报 "
            "'Neither ANDROID_HOME nor ANDROID_SDK_ROOT environment variable was exported'）？"
        )

    yield drv
    drv.quit()


@pytest.fixture(scope="function")
def app_package(caps):
    """被测 App 包名，统一从配置读取（不要从 driver.capabilities 里猜）。"""
    return caps["appPackage"]


@pytest.fixture(scope="function")
def login_page(driver, app_package, caps):
    """每条用例从登录页开始。

    注意：直接 terminate + activate 时，Android 往往会恢复之前的 Activity 栈
    （也就是又回到商店页），于是后续定位会白等。所以这里用 intent 显式拉起
    启动页 Activity，保证每次真的从登录页开始。
    """
    from pages.pages import LoginPage

    activity = caps["appActivity"].lstrip(".")
    driver.terminate_app(app_package)
    driver.execute_script("mobile: startActivity", {
        "intent": f"{app_package}/{app_package}.{activity}",
    })
    return LoginPage(driver)


@pytest.fixture(scope="function")
def shop_page(login_page):
    """登录成功后的商店页，供购买/支付用例直接使用。"""
    from pages.pages import ShopPage

    login_page.login("user1", "123456")
    shop = ShopPage(login_page.driver)
    assert shop.is_shop_displayed, "登录后应进入商店页"
    return shop
