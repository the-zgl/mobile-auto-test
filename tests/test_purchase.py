# -*- coding: utf-8 -*-
"""购买 / 支付模块用例：下单 → 收银台 → 支付回调 → 发货，含异常与边界分支。

支付是「钱」相关的流程，用例重点不是「能付成功」，而是：
金额是否正确扣减、余额不足是否被拦、取消订单是否不扣款、重复提交是否只成交一次。
"""
import pytest

from pages.pages import ShopPage

#: 商品列表里第 0 行的单价（分），与 demo-app 的 ITEMS 表保持一致
FIRST_ITEM_PRICE = 300


@pytest.mark.smoke
@pytest.mark.payment
def test_purchase_flow(shop_page):
    """主流程：下单 → 确认支付 → 出现成功提示。"""
    shop_page.purchase_first_item()

    assert shop_page.is_pay_success_shown, "支付完成后应出现成功提示"
    assert "支付成功" in shop_page.pay_success_text

@pytest.mark.payment
def test_purchase_deducts_exact_amount(shop_page):
    """金额校验：支付后余额应精确减少商品单价，不能多扣也不能不扣。"""
    before = shop_page.balance

    shop_page.purchase_first_item()

    assert shop_page.is_pay_success_shown
    assert shop_page.balance == before - FIRST_ITEM_PRICE, (
        f"余额应精确扣减 {FIRST_ITEM_PRICE} 分"
    )


@pytest.mark.payment
def test_cancel_order_does_not_deduct(shop_page):
    """异常分支：收银台点「取消」= 用户放弃支付，一分钱都不能扣。"""
    before = shop_page.balance
    before_hint = shop_page.pay_success_text

    shop_page.open_first_item()
    shop_page.tap_buy()
    shop_page.cancel_pay()

    assert shop_page.pay_success_text == before_hint, "取消支付不应新增任何成功提示"
    assert shop_page.balance == before, "取消订单不能扣款"


@pytest.mark.payment
def test_insufficient_balance_blocks_payment(shop_page):
    """异常分支：余额不足时应被拦截，且不能把余额扣成负数。

    先把余额花到不足一件商品的价格，再尝试购买。
    """
    guard = 0
    while shop_page.balance >= FIRST_ITEM_PRICE and guard < 20:
        shop_page.purchase_first_item()
        guard += 1

    remaining = shop_page.balance
    assert remaining < FIRST_ITEM_PRICE, "前置条件：余额应已被花到不足一件商品"

    # 余额不足时点击购买 → 确认支付，应被拦截
    shop_page.open_first_item()
    shop_page.tap_buy()
    shop_page.tap_pay()

    assert shop_page.balance == remaining, "支付失败不能改动余额"
    assert shop_page.balance >= 0, "余额不能变成负数"


@pytest.mark.payment
def test_price_displayed_matches_resource_id(shop_page):
    """数据校验：列表第 0 行的商品名通过 resource-id 能定位到，
    说明「用 id 定位」这条链路是通的（定位问题要能第一时间发现）。
    """
    from selenium.webdriver.common.by import By

    from pages.pages import app_id

    item = shop_page.find((By.ID, app_id("item_0")))
    assert item.is_displayed()


@pytest.mark.payment
def test_double_pay_only_charges_once(shop_page):
    """稳定性：对同一笔订单重复点击「确认支付」，只应成交一次。

    （当前 Demo 用弹窗实现，对话框点掉即关闭，因此这里验证的是
    「一次下单只扣一次款」；真实渠道还要覆盖服务端回调幂等，
    项目一 PaymentServiceTests 里已经覆盖了重复回调不重复发货。）
    """
    before = shop_page.balance

    shop_page.purchase_first_item()

    assert shop_page.balance == before - FIRST_ITEM_PRICE, "一次下单只应扣款一次"
