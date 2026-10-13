# -*- coding: utf-8 -*-
"""页面对象：登录页（账号）与商店页（购买 / 支付）。

元素定位统一走 resource-id（By.ID），比 XPath 快且稳定。
如果被测 App 改版换掉了 id，只需要改这个文件，用例层不用动 —— 这就是 POM 的价值。
"""
from selenium.webdriver.common.by import By

from pages.base_page import BasePage

#: 被测 App 包名（与 demo-app/app/build.gradle 里的 applicationId 一致）
APP_PACKAGE = "com.daping.demoshop"


def app_id(name):
    """拼出 Android 的 resource-id 全名：包名:id/控件名。"""
    return f"{APP_PACKAGE}:id/{name}"


class LoginPage(BasePage):
    """登录页（账号模块）。"""

    USERNAME = (By.ID, app_id("username"))
    PASSWORD = (By.ID, app_id("password"))
    LOGIN_BTN = (By.ID, app_id("login"))
    ERROR_MSG = (By.ID, app_id("error"))

    def login(self, username, password):
        """填写账号密码并点击登录（不做断言，断言留给用例层）。"""
        self.input_text(self.USERNAME, username)
        self.input_text(self.PASSWORD, password)
        self.hide_keyboard_if_shown()
        self.tap(self.LOGIN_BTN)
        return self

    def login_expect_failure(self, username, password):
        """点击登录后等待错误提示出现（失败分支专用）。"""
        self.login(username, password)
        self.wait.until(lambda d: self._error_text_now() != "")
        return self

    def _error_text_now(self):
        try:
            return self.driver.find_element(*self.ERROR_MSG).text.strip()
        except Exception:
            return ""

    @property
    def error_message(self):
        return self._error_text_now()

    @property
    def is_error_displayed(self):
        return self.is_displayed(self.ERROR_MSG, timeout=5)


class ShopPage(BasePage):
    """商店页 + 收银台（购买 / 支付模块）。"""

    FIRST_ITEM = (By.ID, app_id("item_0"))
    BUY_BTN = (By.ID, app_id("btn_buy"))
    BALANCE = (By.ID, app_id("tv_balance"))
    PAY_SUCCESS = (By.ID, app_id("tv_pay_success"))

    #: 收银台弹窗里的「确认支付」按钮：系统对话框，用文案定位
    PAY_CONFIRM = (By.XPATH, "//*[@text='确认支付']")
    PAY_CANCEL = (By.XPATH, "//*[@text='取消']")
    DIALOG_TITLE = (By.XPATH, "//*[@text='收银台']")

    # ------------------------------------------------------------------ 操作

    def open_first_item(self):
        self.tap(self.FIRST_ITEM)
        return self

    def tap_buy(self):
        """点「购买」= 下单，应当弹出收银台确认框。"""
        self.tap(self.BUY_BTN)
        return self

    def tap_pay(self):
        """点「确认支付」= 支付回调 + 发货。"""
        self.tap(self.PAY_CONFIRM)
        return self

    def cancel_pay(self):
        self.tap(self.PAY_CANCEL)
        return self

    def purchase_first_item(self):
        """下单 → 确认支付 的完整链路。"""
        self.open_first_item()
        self.tap_buy()
        self.tap_pay()
        return self

    # ------------------------------------------------------------------ 断言辅助

    @property
    def balance_text(self):
        return self.get_text(self.BALANCE)

    @property
    def balance(self):
        """把「余额：1000 分」解析成整数 1000，方便做数值断言。"""
        text = self.balance_text
        digits = "".join(ch for ch in text if ch.isdigit())
        return int(digits) if digits else -1

    @property
    def pay_success_text(self):
        return self.get_text(self.PAY_SUCCESS)

    @property
    def is_pay_success_shown(self):
        return self.is_displayed(self.PAY_SUCCESS, timeout=5)

    @property
    def is_shop_displayed(self):
        """商店页是否已经加载完成（用余额控件判断，比固定 sleep 可靠）。"""
        return self.is_displayed(self.BALANCE)
