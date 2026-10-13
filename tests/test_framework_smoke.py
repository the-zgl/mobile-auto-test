# -*- coding: utf-8 -*-
"""框架自检用例：不需要连接设备，CI 里必跑。

这类「测试的测试」很关键：它保证配置能读、页面对象能导入、定位符格式正确，
这样在真机上跑失败时，你可以立刻判断「是框架坏了」还是「是被测 App 变了」。
"""
import glob
import os
import xml.etree.ElementTree as ET

import pytest

from pages.pages import APP_PACKAGE, LoginPage, ShopPage, app_id

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _find_demo_layouts():
    """定位 demo-app 的布局目录，兼容「从仓库根目录」和「从子目录」两种执行方式。"""
    patterns = [
        os.path.join(REPO_ROOT, "demo-app", "app", "src", "main", "res", "layout", "*.xml"),
        os.path.join(REPO_ROOT, "mobile-auto-test", "demo-app", "app", "src",
                     "main", "res", "layout", "*.xml"),
    ]
    for pattern in patterns:
        found = glob.glob(pattern)
        if found:
            return found
    return []


def _find_demo_res_values():
    """定位 demo-app 的 res/values 目录（ids.xml 里声明了 ListView 各行 id）。"""
    patterns = [
        os.path.join(REPO_ROOT, "demo-app", "app", "src", "main", "res", "values"),
        os.path.join(REPO_ROOT, "mobile-auto-test", "demo-app", "app", "src",
                     "main", "res", "values"),
    ]
    for path in patterns:
        if os.path.isdir(path):
            return path
    return None


def test_config_file_readable(config):
    """配置文件应存在、可解析，且关键字段不缺。"""
    assert config.get("appium", {}).get("url"), "config.yaml 缺少 appium.url"

    caps = config.get("caps", {})
    for key in ("platformName", "deviceName", "appPackage", "appActivity"):
        assert caps.get(key), f"config.yaml 的 caps 缺少 {key}"


def test_locator_id_format():
    """定位符必须是 Android 合法的 resource-id 全名。"""
    assert app_id("login") == f"{APP_PACKAGE}:id/login"
    assert ":" in app_id("login") and "/" in app_id("login")


def test_page_objects_expose_expected_locators():
    """页面对象应暴露用例依赖的定位符（防止改名后用例静默失效）。"""
    for name in ("USERNAME", "PASSWORD", "LOGIN_BTN", "ERROR_MSG"):
        assert hasattr(LoginPage, name), f"LoginPage 缺少 {name}"

    for name in ("FIRST_ITEM", "BUY_BTN", "PAY_CONFIRM", "BALANCE", "PAY_SUCCESS"):
        assert hasattr(ShopPage, name), f"ShopPage 缺少 {name}"


def test_demo_app_layouts_are_valid_xml_and_contain_expected_ids():
    """被测 App 的布局必须能解析，并且真的存在这些 id。

    这是「用例与控件契约」的静态校验：不连设备也能发现
    「用例改了 id、App 没改」这种最常见的低级事故。
    """
    layouts = _find_demo_layouts()
    if not layouts:
        pytest.skip("未找到 demo-app 布局目录，跳过静态校验")

    merged = ""
    for path in layouts:
        ET.parse(path)  # XML 不合法会直接抛异常
        with open(path, encoding="utf-8") as f:
            merged += f.read()

    for control_id in ("username", "password", "login", "error",
                       "tv_balance", "tv_pay_success", "btn_buy"):
        assert f'@+id/{control_id}"' in merged, f"布局里缺少 @+id/{control_id}"


def test_list_row_ids_are_declared_in_resources():
    """ListView 各行用的 id 必须在资源里声明过。

    R.id.xxx 不是想用就能用的：没有资源声明，AGP 编译期就会报
    `cannot find symbol: variable item_0`。这条用例把「用例要用的 id」
    和「App 真实声明过的 id」对齐，避免测试脚本引用一个根本不存在的控件。
    """
    layouts = _find_demo_layouts()
    values_dir = _find_demo_res_values()
    if not layouts or values_dir is None:
        pytest.skip("未找到 demo-app 资源目录，跳过静态校验")

    declared = ""
    for name in os.listdir(values_dir):
        if name.endswith(".xml"):
            with open(os.path.join(values_dir, name), encoding="utf-8") as f:
                declared += f.read()

    merged_layouts = ""
    for path in layouts:
        with open(path, encoding="utf-8") as f:
            merged_layouts += f.read()

    for row_id in ("item_0", "item_1", "item_2", "item_3", "item_4"):
        in_values = f'name="{row_id}"' in declared
        in_layout = f'@+id/{row_id}"' in merged_layouts
        assert in_values or in_layout, (
            f"控件 {row_id} 既没有在 res/values 里声明，也没有出现在布局中"
        )


def test_manifest_and_config_package_are_consistent():
    """config.yaml 的 appPackage 必须与 Android 工程的 applicationId 一致。"""
    build_gradle = os.path.join(REPO_ROOT, "demo-app", "app", "build.gradle")
    if not os.path.isfile(build_gradle):
        build_gradle = os.path.join(REPO_ROOT, "mobile-auto-test", "demo-app", "app", "build.gradle")
    if not os.path.isfile(build_gradle):
        pytest.skip("未找到 demo-app 的 build.gradle，跳过一致性校验")

    with open(build_gradle, encoding="utf-8") as f:
        content = f.read()

    assert f'applicationId "{APP_PACKAGE}"' in content, (
        f"build.gradle 的 applicationId 与 config.yaml 的 appPackage（{APP_PACKAGE}）不一致"
    )
