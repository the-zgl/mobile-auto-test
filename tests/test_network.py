# -*- coding: utf-8 -*-
"""弱网 / 断网专项测试用例。

被测 App（猫咪商城 Demo）的支付是**本地模拟**（SharedPreferences + 内存），
不依赖真实网络请求。所以这里的专项断言目标不是"请求会不会超时"，
而是：

1. 断网 / 切网时 App **不崩溃**（ANR、Crash）
2. UI **仍可交互**，页面跳转正常
3. 网络切换**不影响业务数据的正确性**（余额、提示文案不串）
4. 网络恢复后功能**完全正常**

这对应 JD 里「了解客户端性能、弱网、适配等专项测试」的要求。
真实项目里同样的框架换成有网络请求的 App，就能直接测
「弱网下支付是否重复提交 / 掉单 / 是否给出明确提示」。

**环境限制（重要）**：
雷电模拟器的 adb 通过 host 网络端口连接，任何「关闭设备网络」的命令
（飞行模式 / svc data disable / svc wifi disable）都会把 adb 连接本身一起断掉，
导致设备 offline 且无法远程恢复。因此这些用例在雷电上会**自动跳过**；
在 AVD 或真机上会正常执行。详见 `helpers/network_condition.py` 的说明。
"""
import pytest

from helpers.network_condition import NetworkCondition
from pages.pages import ShopPage

pytestmark = pytest.mark.network


@pytest.fixture
def network(driver):
    """网络环境模拟器；若当前环境不支持网络切换则跳过用例。"""
    net = NetworkCondition(driver)
    if not net.probe():
        pytest.skip(
            "当前设备不支持「不断 adb」的网络切换（雷电模拟器关闭网络会顺带断掉 adb）。"
            "请在 AVD 或真机上运行本文件以验证弱网场景。"
        )
    return net


def test_offline_app_still_usable(login_page, network):
    """断网后 App 仍可用：能登录、能进商店、控件可点。"""
    network.go_wifi_only()

    login_page.login("user1", "123456")
    shop = ShopPage(login_page.driver)
    assert shop.is_shop_displayed, "断网不应影响本地流程，应仍能进入商店页"


def test_offline_purchase_still_works(login_page, network):
    """断网下购买流程仍正确（本地业务不依赖网络）。"""
    network.go_wifi_only()

    login_page.login("user1", "123456")
    shop = ShopPage(login_page.driver)
    before = shop.balance

    shop.purchase_first_item()

    assert shop.is_pay_success_shown, "断网不应阻断本地购买"
    assert shop.balance == before - 300, "断网下余额仍应精确扣减"


def test_network_switch_does_not_corrupt_balance(login_page, network):
    """在断网 / 恢复之间反复切换，余额与提示文案不应错乱。"""
    login_page.login("user1", "123456")
    shop = ShopPage(login_page.driver)
    before = shop.balance

    # 切到仅 WiFi → 买一次
    network.go_wifi_only()
    shop.purchase_first_item()
    after_switch = shop.balance
    assert after_switch == before - 300, "切网后购买，余额应正确"

    # 恢复网络 → 再买一次
    network.restore()
    shop.purchase_first_item()
    after_restore = shop.balance
    assert after_restore == after_switch - 300, "恢复网络后再买，余额应继续正确累加"

    # 提示文案应只反映最后一次
    assert "支付成功" in shop.pay_success_text


def test_restore_network_after_switch(login_page, network):
    """网络恢复后功能完全正常（验证 restore 真的生效）。"""
    network.go_wifi_only()
    network.restore()

    login_page.login("user1", "123456")
    shop = ShopPage(login_page.driver)
    before = shop.balance
    shop.purchase_first_item()
    assert shop.balance == before - 300, "网络恢复后购买应正常"
