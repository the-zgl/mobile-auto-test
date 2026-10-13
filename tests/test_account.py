# -*- coding: utf-8 -*-
"""账号模块用例：登录成功 / 密码错误 / 空值校验 / 重复登录。

用例设计思路（面试可讲）：
按「正常值 → 异常值 → 边界值」拆，而不是只写一条「能登录就行」。
"""
import pytest

from pages.pages import ShopPage


@pytest.mark.smoke
@pytest.mark.account
def test_login_success(login_page):
    """正常路径：正确账号密码应进入商店页。"""
    login_page.login("user1", "123456")

    shop = ShopPage(login_page.driver)
    assert shop.is_shop_displayed, "登录成功后应进入商店首页"


@pytest.mark.account
def test_login_fail_wrong_password(login_page):
    """异常路径：密码错误应停留登录页并给出提示。"""
    # 用 login_expect_failure：它会等到错误提示真的出现，
    # 避免在慢设备上「点击后立刻断言」读到空字符串而偶发失败
    login_page.login_expect_failure("user1", "wrong-pass")

    assert "密码错误" in login_page.error_message, "密码错误时应提示「密码错误」"


@pytest.mark.parametrize(
    "username,password,expected",
    [
        ("", "123456", "请输入账号和密码"),
        ("user1", "", "请输入账号和密码"),
        ("not-exist", "123456", "密码错误"),
    ],
    ids=["空账号", "空密码", "账号不存在"],
)
@pytest.mark.account
def test_login_invalid_input(login_page, username, password, expected):
    """边界路径：空值与不存在的账号都不应放行。"""
    login_page.login_expect_failure(username, password)

    assert expected in login_page.error_message


@pytest.mark.account
def test_login_repeated_click_does_not_duplicate_balance(login_page, app_package):
    """稳定性：反复登录，不应重置或重复累加余额。

    这类「重复提交」用例是账号/支付模块的必测项：
    用户手抖连点两次，不能变成两次业务动作。
    """
    from pages.pages import LoginPage, ShopPage

    login_page.login("user1", "123456")
    shop = ShopPage(login_page.driver)
    assert shop.is_shop_displayed
    first_balance = shop.balance

    # 杀进程后用 intent 显式回到登录页，再登一次。
    # terminate_app 在某些设备上不可靠，_wait_until_app_not_running 会用 adb force-stop 兜底。
    login_page.driver.terminate_app(app_package)
    _wait_until_app_not_running(login_page.driver, app_package)
    login_page.driver.execute_script("mobile: startActivity", {
        "intent": f"{app_package}/{app_package}.LoginActivity",
    })
    _wait_until_activity_resumed(login_page.driver, "LoginActivity")

    LoginPage(login_page.driver).login("user1", "123456")
    again = ShopPage(login_page.driver)
    assert again.is_shop_displayed
    assert again.balance == first_balance, "重复登录不应重置或重复累加余额"


def _wait_until_app_not_running(driver, app_package, timeout=15):
    """等到被测 App 不在前台运行。

    两个坑：
    1. Appium 的 terminate_app 在部分设备/ROM 上不可靠（命令返回成功但进程还在），
       所以用 adb force-stop 兜底；
    2. query_app_state 的取值是 0=未安装 1=未运行 2=后台挂起 3=后台 4=前台，
       判「已退出」应该用「不等于 4」，写成 ==4 会永远等不到。
    """
    import subprocess

    from selenium.webdriver.support.ui import WebDriverWait

    adb = _find_adb()
    device = driver.capabilities.get("deviceUDID") or driver.capabilities.get("udid")
    cmd = [adb] + (["-s", device] if device else []) + ["shell", "am", "force-stop", app_package]
    subprocess.run(cmd, capture_output=True, text=True, errors="replace")

    def _stopped(d):
        # Appium query_app_state: 0=未安装 1=未运行 2=后台挂起 3=后台 4=前台运行
        # 所以「已退出」= 不等于 4
        try:
            return d.query_app_state(app_package) != 4
        except Exception:
            return False

    WebDriverWait(driver, timeout).until(_stopped, message=f"{app_package} 未在 {timeout}s 内退出")


def _find_adb():
    import os

    for candidate in (
        os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb"),
        os.path.join(os.environ.get("ANDROID_SDK_ROOT", ""), "platform-tools", "adb"),
        "adb",
    ):
        if candidate == "adb" or os.path.isfile(candidate) or os.path.isfile(candidate + ".exe"):
            return candidate
    return "adb"


def _wait_until_activity_resumed(driver, activity_name, timeout=20):
    """等到指定 Activity 真正处于前台，避免操作打在旧页面上。"""
    from selenium.webdriver.support.ui import WebDriverWait

    def _resumed(d):
        current = d.current_activity or ""
        return activity_name in current

    WebDriverWait(driver, timeout).until(_resumed, message=f"{activity_name} 未在 {timeout}s 内成为前台")
