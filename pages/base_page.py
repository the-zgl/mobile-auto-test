# -*- coding: utf-8 -*-
"""页面基类：封装显式等待 + 查找、点击、输入、断言。

测试稳定性设计：
不用 time.sleep()，统一用 WebDriverWait 显式等待；
不用隐式等待硬扛，因为它对「元素已存在但不可见」这类场景无效。
"""
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """所有页面对象的父类。子类只声明 locator，行为逻辑收在这里。"""

    #: 显式等待超时（秒）
    TIMEOUT = 15

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, self.TIMEOUT)

    # ------------------------------------------------------------- 基础操作

    def find(self, locator):
        """等待元素出现在 DOM 中并返回（tuple 形式：(By.XX, "value")）。"""
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_all(self, locator):
        return self.driver.find_elements(*locator)

    def tap(self, locator):
        """等待可点击后点击：能规避「页面刚切换、控件还没就绪」的偶发失败。"""
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()
        return element

    def input_text(self, locator, text):
        element = self.find(locator)
        element.clear()
        element.send_keys(text)
        return element

    def get_text(self, locator):
        return self.find(locator).text

    def is_displayed(self, locator, timeout=None):
        """在超时时间内出现过就返回 True，否则返回 False（不抛异常）。"""
        try:
            WebDriverWait(self.driver, timeout or self.TIMEOUT).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except Exception:
            return False

    def exists(self, locator):
        """元素是否存在于 DOM（不要求可见）。"""
        return len(self.find_all(locator)) > 0

    # --------------------------------------------------------- 设备/应用行为

    @property
    def current_activity(self):
        return self.driver.current_activity

    def back(self):
        self.driver.back()

    def hide_keyboard_if_shown(self):
        """输入完成后收起软键盘，避免键盘遮挡按钮导致点击失败。"""
        try:
            if self.driver.is_keyboard_shown():
                self.driver.hide_keyboard()
        except Exception:
            # 部分设备/驱动不支持，忽略即可
            pass

    def restart_app(self, app_package):
        """杀掉并重开被测 App（不是清数据，只是重启进程）。

        注意：Android 恢复时可能回到之前的 Activity 栈，
        需要「一定回到首页」时请用 driver.terminate_app + 启动页 Activity 显式拉起。
        """
        self.driver.terminate_app(app_package)
        self.driver.activate_app(app_package)
