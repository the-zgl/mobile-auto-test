# 移动端自动化测试框架（Appium + pytest + CI）

![CI](https://github.com/the-zgl/mobile-auto-test/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Appium](https://img.shields.io/badge/Appium-2.19.0-green)
![pytest](https://img.shields.io/badge/pytest-18%20tests-brightgreen)

一个 **移动端测试开发** 方向的实践项目：一套按 **Page Object Model** 分层的 Android 自动化测试框架，
覆盖「**账号登录**」与「**购买 / 支付**」两条核心业务链路，自带被测 App，接入 **GitHub Actions** 持续集成。

> 目标：克隆下来就能真实跑通的测试工程，而不是只能看的示例代码。
>
> **当前状态（实测，非设想）**：已在 **Android 9（API 28）/ x86_64 模拟器**上
> **连续多次全量 18 条用例全部通过（`18 passed`，单次约 2 分 20 秒 ~ 2 分 40 秒）**，
> HTML 报告生成在 `reports/report.html`；`gradlew assembleDebug` **BUILD SUCCESSFUL**，
> APK 约 **3.02 MB**，`adb install -r` 返回 **Success**。
> **未验证项**：没有在**真机（ARM）**上跑过（只在 x86_64 模拟器验证）。

## 技术要点

本项目主要覆盖以下技术点：

| 技术点 | 实现方式 |
|---|---|
| Python | 框架、用例、CI 校验脚本全部 Python |
| Appium / 移动端测试框架 | Appium + UiAutomator2，POM 分层，显式等待 |
| 自动化用例设计、维护 | 18 条用例按「正常 / 异常 / 边界」设计，数据驱动（`parametrize`） |
| CI/CD 对接 | GitHub Actions：语法检查、控件契约校验、用例收集、免设备用例、可选真机 job |
| 账号、支付业务测试要点 | 登录成功/失败/空值/重复登录；下单→收银台→支付、余额精确扣减、取消不扣款、余额不足拦截、重复支付只成交一次 |
| 测试平台 / 质量中台 | 产出 pytest-html / Allure 报告，为后续「用例+结果+报告」网页化打基础 |

## 一句话介绍

用 **pytest + Appium + POM** 组织移动端自动化用例，用**自研被测 App（DemoShop）**保证测试对象可控，
用 **GitHub Actions** 把「静态校验 + 用例收集 + 免设备用例」卡进每次 push。

## 目录结构

```
mobile-auto-test/
├── config/
│ └── config.yaml # Appium 服务地址 + deviceName / 包名 / 启动页（当前为 Android 9）
├── pages/
│ ├── base_page.py # 页面基类：显式等待、点击、输入、断言、收起键盘
│ └── pages.py # LoginPage（账号）/ ShopPage（购买·支付）
├── tests/
│ ├── test_account.py # 账号用例：成功 / 密码错误 / 空值 / 重复登录（6 条，需设备）
│ ├── test_purchase.py # 支付用例：主流程 / 金额 / 取消 / 余额不足 / 重复支付（6 条，需设备）
│ └── test_framework_smoke.py # 免设备自检：配置、定位符、控件契约、包名一致性（6 条）
├── demo-app/ # 自研被测 App（Android，Java + AndroidX）
│ ├── gradlew / gradlew.bat # ✅ 仓库已含 Gradle wrapper 8.7，无需自行生成
│ ├── gradle/wrapper/ # ✅ gradle-wrapper.jar + gradle-wrapper.properties
│ ├── local.properties # 本机 SDK 路径（在 .gitignore 中，不入库）
│ └── app/src/main/
│ ├── java/com/daping/demoshop/{LoginActivity,MainActivity}.java
│ ├── res/layout/{activity_login,activity_main,item_product}.xml
│ └── AndroidManifest.xml
├── conftest.py # fixture：config / caps / driver / login_page / shop_page
│ # + --no-device / --keep-app-data；建会话前 pm clear 清数据
├── pytest.ini # 用例目录、marker 注册（smoke / account / payment）
├── requirements.txt
├── .github/workflows/ci.yml # CI 流水线
└── README.md
```

## 被测 App（demo-app）说明

| 项目 | 值 |
|---|---|
| applicationId | `com.daping.demoshop` |
| 启动页 | `.LoginActivity` |
| 测试账号 | `user1` / `123456` |
| 初始余额 | 1000 分（首次登录时初始化，重复登录不会重置） |
| 商品 | 猫粮礼包 300 / 逗猫棒 150 / 猫抓板 450 / 小鱼干 100 / 猫窝 800（分） |

**为什么自己写被测 App**：真实项目里测试对象是别人的 App，练手时容易卡在「没有 App 可测」。
自学时自研一个可控的 App，好处是：控件 id 稳定、支付分支可以随意构造（余额不足、取消订单），
而且「用例 id 与布局 id 一致性」可以被静态校验守住。

## 环境准备

| 组件 | 要求 | 说明 |
|---|---|---|
| Python | 3.10+ | `pip install -r requirements.txt` |
| JDK | 17+ | Android Gradle Plugin 8.5 要求 JDK 17；Android Studio 自带 JBR 也可 |
| Android SDK | 任意较新版本 | 需含 `platform-tools`（adb）；工程 `compileSdk 34` |
| Node.js | 16.13+ / 18+ / 20+ | **Node 版本决定 Appium 可选版本**，见下方版本矩阵 |
| Appium | 2.x（推荐 2.19.0） | 配 `uiautomator2` 4.2.1，理由见下 |
| 设备 | Android 9+ 模拟器或真机 | `adb devices` 能看到即可 |

**版本矩阵（这条是实测出来的，不是抄的）**

| Node 版本 | 可用 Appium | 可用 uiautomator2 驱动 |
|---|---|---|
| 16.13+ | **2.x**（如 2.19.0） | **4.x**（如 4.2.1） |
| 20.19+ | 2.x 或 3.x | 4.x 或 5.x+ |

直接 `npm install -g appium` 会装到最新版（3.x），而 3.x 的 `engines.node` 要求
`^20.19.0 || ^22.12.0 || >=24.0.0`；在 Node 16 上启动即崩，报
`TypeError: (0 , U.tracingChannel) is not a function`。
同理 `appium-uiautomator2-driver` 5.0.0 及以上也要求 Node ≥ 20.19。
所以**版本必须成套锁死**，仓库 CI 里锁的是 `appium@2.19.0` + `uiautomator2@4.2.1`。

**1. Python 依赖**

```powershell
python --version          # 期望 3.10+
pip install -r requirements.txt
```

**2. 设置 JDK 与 Android SDK 环境变量**

```powershell
# 按你本机的实际路径修改下面两个值
$env:JAVA_HOME = "<你的 JDK 17 路径>"
$env:ANDROID_HOME = "<你的 Android SDK 路径>"     # 通常是 %LOCALAPPDATA%\Android\Sdk
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME

# 先证明路径存在，再谈构建
Test-Path "$env:JAVA_HOME\bin\java.exe"       # 应为 True
Test-Path "$env:ANDROID_HOME\platform-tools\adb.exe"  # 应为 True
```

> 踩过的坑：`JAVA_HOME` 设成一个**不存在的目录**时，`java -version` 仍可能因为 PATH 里有
> 别的 Java 而「看起来正常」，但 Gradle 会用 `JAVA_HOME`，最后在编译期才报错。
> 所以要用 `Test-Path` 确认目录真实存在。

**3. 安装 Appium（成套锁版本）**

```powershell
npm install -g appium@2.19.0
appium driver install uiautomator2@4.2.1
appium --version          # 期望 2.19.0
```

**4. 启动 Appium 时必须带上 `ANDROID_HOME`**

```powershell
$env:ANDROID_HOME = "<你的 Android SDK 路径>"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
appium
```

> 环境变量必须和 `appium` 命令在**同一个终端窗口**里设置，否则连设备时报
> `Neither ANDROID_HOME nor ANDROID_SDK_ROOT environment variable was exported`。
> 这条也已写进 `conftest.py` 连接失败时的排查清单。

**5. 确认设备在线**

```powershell
adb devices               # 必须看到一台 state 为 device 的设备
```

## 部署与运行

```powershell
# 1) 编译并安装被测 App（wrapper 已在仓库里，直接用它，不要重新生成）
cd demo-app
.\gradlew assembleDebug
adb install -r app\build\outputs\apk\debug\app-debug.apk

# 2) 启动 Appium 服务（新开一个窗口，带 ANDROID_HOME）
appium

# 3) 按你的设备改配置
cd ..
notepad config\config.yaml        # 改 deviceName / platformVersion

# 4) 跑用例
pytest -m smoke                                    # 只跑冒烟
pytest                                             # 全量
pytest --html=reports/report.html --self-contained-html   # 带 HTML 报告
```

`config/config.yaml` 里需要按你的环境改两项：

```yaml
caps:
  deviceName: "emulator-5554"    # 用 `adb devices` 看到的设备名
  platformVersion: "9"           # 用 `adb shell getprop ro.build.version.release` 查
```

> **多台设备时务必锁死设备**：`conftest.py` 除了设 `deviceName`，还会设 `udid`。
> 只设 `deviceName` 时 Appium 会自己挑一台设备，可能连到**没装被测 App** 的那台上，
> 报 `Activity name '.LoginActivity' ... doesn't exist or cannot be launched!`
> 这是「连错设备」的典型症状，不是 App 的问题。

### 不连设备也能验证

```powershell
pytest --collect-only -q    # 应输出 18 tests collected
pytest --no-device -q       # 应输出 6 passed, 12 skipped
```

这两条不依赖任何设备与 Appium，用于在干净环境里确认「框架本身是好的」。
`--no-device` 模式下依赖 `driver` 的用例会被跳过，只有 6 条框架自检用例真正执行。

### 已验证事实（在什么环境、什么结果）

- 全量 **18 条用例**在 **Android 9（API 28）/ x86_64 模拟器**上跑绿，单次约 2 分 20 秒。
- `gradlew assembleDebug` **BUILD SUCCESSFUL**，APK 约 **3.02 MB**，`adb install -r` 返回 Success。
- 连续多次全量均 18/18 通过（用于排除偶发失败）。
- **未验证**：没有在 ARM 真机上跑过。真机的 adb 连接方式、性能表现与 x86_64 模拟器不同，
  因此本文档对 App 行为的描述基于「模拟器实跑观测 + 源码逻辑」，不含 ARM 真机结论。

### 用例之间的状态隔离

`conftest.py` 的 `driver` fixture 在**建立 Appium 会话之前**会执行
`adb shell pm clear <包名>`，把 App 数据（余额、残留提示文案）清干净，
保证每条用例都从同一个确定起点开始。

```powershell
pytest --keep-app-data       # 想观察「连续状态」时，用这个参数跳过清理
```

## 用例清单（18 条 = 14 条需设备 + 4 条免设备）

**账号模块（`tests/test_account.py`，6 条，需设备）**
- `test_login_success`：正确账号密码 → 进入商店页
- `test_login_fail_wrong_password`：密码错误 → 停留登录页并提示
- `test_login_invalid_input`：空账号 / 空密码 / 账号不存在（数据驱动 3 条）
- `test_login_repeated_click_does_not_duplicate_balance`：重复登录不重置、不重复累加余额

**支付模块（`tests/test_purchase.py`，6 条，需设备）**
- `test_purchase_flow`：下单 → 确认支付 → 出现成功提示
- `test_purchase_deducts_exact_amount`：余额精确扣减 300 分
- `test_cancel_order_does_not_deduct`：点「取消」一分钱都不能扣，**且成功提示文案与操作前一致**
- `test_insufficient_balance_blocks_payment`：余额不足被拦截，余额不为负
- `test_price_displayed_matches_resource_id`：用 resource-id 能正确定位到商品行
- `test_double_pay_only_charges_once`：一次下单只扣一次款

**框架自检（`tests/test_framework_smoke.py`，6 条，免设备）**
- 配置可读、定位符格式合法、页面对象暴露预期定位符、
 demo-app 布局 XML 合法且包含预期控件 id、`config.yaml` 的包名与 `build.gradle` 一致、
 ListView 各行的 `item_0`~`item_4` 已在资源中声明（否则 `R.id.item_0` 编译期就报错）
**弱网 / 断网专项（`tests/test_network.py`，4 条，需设备）**
- `test_offline_app_still_usable`：断开数据网络后仍能登录、进商店、控件可点
- `test_offline_purchase_still_works`：断网下本地购买流程仍正确，余额精确扣减
- `test_network_switch_does_not_corrupt_balance`：断网 / 恢复之间反复切换，余额与提示文案不错乱
- `test_restore_network_after_switch`：网络恢复后功能完全正常

> 被测 App 的支付是**本地模拟**（不依赖真实网络请求），所以弱网用例的断言重点是
> 「不崩溃、UI 可用、业务数据不错乱」；换成有真实网络请求的 App，同一套框架即可直接验证
> 「弱网下支付是否重复提交 / 掉单 / 是否给出明确提示」。

## 弱网测试：实现方式与踩坑（实测结论）

`helpers/network_condition.py` 封装了网络环境切换。以下都是**在本机实测出来**的结论：

| 方案 | 在雷电模拟器上的结果 |
|---|---|
| `driver.set_network_speed("gsm" / "lte")` | 不可用。它依赖 AVD 的 `-netspeed` 参数，报 `Error executing adbExec` |
| `driver.set_network_connection(2)`（内部走 `svc data disable`） | 会把进程杀掉（exit 137 / `call killProcess`） |
| `adb shell svc wifi disable` | 同样导致设备 offline |
| `adb shell settings put global airplane_mode_on 1` | 能进飞行模式，但 adb 一并断开，设备 offline 后**无法远程恢复**，只能重启模拟器 |

**根本原因**：雷电模拟器的 adb 通过 **host 网络端口**连接（而非本地管道），
所以任何「关闭设备网络」的操作都会把 adb 连接本身一起断掉。
AVD 用本地管道，不受此影响 —— 这正是 `set_network_speed` / 网络切换
在 AVD 上正常、在雷电上不可用的原因。

**工程处理**：`NetworkCondition.probe()` 会**真的做一次最小切换再切回**，
然后确认 adb 是否仍然在线；不在线就判定「本环境不支持」，用例 `pytest.skip`
并给出可读原因。这样在雷电上是 skipped（不是 failed），在 AVD / 真机上会真实执行。

> 注意：只跑只读命令（如 `dumpsys connectivity`）来探测是不够的 ——
> 雷电上它能正常返回 0，但 `svc data disable` 依然会杀进程。必须实测一次写操作。

## 质量看板（测试平台雏形）

`tools/build_dashboard.py` 把 pytest 的 JSON 报告转成一个**静态网页**，
对应测试平台的三件套：

```powershell
# 1) 跑测试并产出 JSON 报告
pytest --json-report --json-report-file=reports/report.json

# 2) 生成质量看板
python tools/build_dashboard.py --input reports/report.json --output reports/report.html
```

页面包含：

1. **用例管理** —— 用例列表 + 模块 / 优先级标签（smoke / account / payment / network）+ 按文件聚合
2. **执行结果** —— 用例总数、通过 / 失败 / 跳过、通过率、总耗时、结论徽章
3. **报告详情** —— 每条用例的结果、失败原因（首行）、执行时长

**设计取舍**：用「静态 HTML + 内嵌数据」而不是起 Web 服务 ——
零依赖（不需要 Flask / Node）、可以直接丢到 GitHub Pages、也能当附件发给别人。
需要登录鉴权、历史趋势、定时调度时，再在这个基础上加后端。


## 踩坑记录：用例间状态污染（`2 failed, 15 passed, 1 error` → 18 全绿）

**这是本项目最有价值的一段经历**：第一次全量跑**不是全绿**，而是
`2 failed, 15 passed, 1 error`。

**① 现象**（失败看起来像被测 App 有 bug）
- `test_purchase_deducts_exact_amount` 失败：「余额精确扣减 300 分」算不平。
- 另一条支付用例失败：期望的扣款金额对不上。
- `test_purchase_flow` 报的是 **ERROR**（不是 FAILED）：上一条失败用例留下了**未关闭的收银台对话框**，
 导致后续会话异常。

**② 根因：用例之间共享了持久化状态**（两个污染源）
| 污染源 | 表现 |
|---|---|
| **余额存在 `SharedPreferences`，跨用例累积** | 前面的用例把 1000 分花到 **100 分**；轮到「扣款 300」的用例时余额已经不够，那条断言在数学上**不可能成立** |
| **支付成功提示文案残留在界面上** | `tv_pay_success` 还挂着上一轮的「支付成功：猫粮礼包 -300 分」，于是负向断言读到了旧文案 |

> 排查技巧：**先分清 `FAILED` 和 `ERROR`**。前者通常是断言不成立，后者通常是环境/会话出了问题
> （这里就是「前一条用例的残骸把后一条搞崩」）。

**③ 修复：三层各改一处**

1. **框架层清数据** —— `conftest.py` 新增 `find_adb` / `clear_app_data` 两个函数，
 在 `driver` fixture 建会话前执行 `adb shell pm clear <包名>`，
 并新增 `--keep-app-data` 参数（与 `--no-device` 并列）用于跳过清理。
2. **App 层清提示** —— `MainActivity.refreshBalance` 里加 `paySuccess.setText("")`，
 进页面时清掉上一轮残留的支付成功提示。
3. **断言改得更精确** —— `test_cancel_order_does_not_deduct` 从「不应出现成功提示」
 改成**记录操作前的文案再比较**：「成功提示文案与操作前一致」。
 （`tv_pay_success` 控件始终存在，所以「元素不可见」这种负向断言在移动端并不可靠。）

**④ 结果**

```text
18 passed in 136.45s (0:02:16)
```

**⑤ 这个修复的价值**
- 它证明的是「**真的在设备上跑过**」而不是「代码写完了」——没跑过的人说不清 `FAILED` 和 `ERROR` 的区别。
- 它讲的是「**测试隔离**」这个核心概念：**持久化状态 + 用例间不重置 = 偶发失败与顺序依赖**。
- 修复分三层（框架 / 被测 App / 断言写法），体现的是**消除根因**而不是「加个 sleep 或重试盖住症状」。
- 顺带回答一个常见疑问：「为什么不用 `pytest-rerunfailures` 重跑？」——
 **状态污染导致的是必现失败，重跑还是会失败，只是把问题藏起来；偶发失败才考虑重试。**


## 踩坑记录 2：全量场景下稳定的偶发失败（单跑全绿、连跑必挂）

**现象**：修好状态污染后，单跑那条用例每次通过，但**放进全量套件里连续 3 次稳定失败**
（1 failed, 17 passed）。失败的是 	est_login_repeated_click_does_not_duplicate_balance，
报错是 `TimeoutException: com.daping.demoshop 未在 15s 内退出`。

**排查过程**（这段比结论更有价值）：

1. 第一反应是"偶发"，于是加等待：`terminate_app` 后轮询进程状态 → **没用**，连续 3 次都超时。
2. 用 `adb shell pidof` / `ps -A` 手动核对，发现 **App 其实早就退出了**（force-stop 后无进程）。
   → 说明不是 App 没退，是**我的判断条件写错了**。
3. 翻 Appium 文档确认 `query_app_state` 的取值语义：

   | 值 | 含义 |
   |---|---|
   | 0 | 未安装 |
   | 1 | 未运行 |
   | 2 | 后台挂起 |
   | 3 | 后台运行 |
   | 4 | **前台运行** |

   我原来写的是 `== 4`，等于在等"App 在前台运行"——App 都退了，永远等不到，必然超时。
   正确写法是 **`!= 4`**。

4. 另外补了两个稳健性处理：`terminate_app` 在某些 ROM 上不可靠（命令返回成功但进程还在），
   所以先 `adb shell am force-stop` 兜底；启动后用 `current_activity` 轮询确认
   `LoginActivity` 真的在前台，避免操作打在旧页面上。

**结果**：原失败组合稳定通过，并**连续 3 次全量 18/18 全绿**。

**这个修复的价值**
- 它示范了排查顺序：**先怀疑自己的判断条件，再怀疑被测对象**。这里 adb 实测证明 App 已退出，
  问题立刻从"App 不听话"转成"我的等待条件写反了"。
- 它暴露了一个常见盲区：**`query_app_state` 的语义不是"有没有退出"，而是"在哪个状态"**。
- 它还说明"单跑通过 ≠ 用例是好的"——**顺序依赖和共享状态**只有放进全量套件才暴露。
## 核心知识点

- **Page Object Model**：元素定位与业务流程分离，App 改版只改一处；用属性（`@property`）把
 「余额：1000 分」解析成整数，断言才能做数值比较
- **fixture 作用域**：`driver` 用 `function` 保证用例隔离；`config`/`caps` 用 `session` 避免重复读盘
- **显式等待 vs 隐式等待**：隐式等待对「元素已存在但不可见」无效，所以统一用 `WebDriverWait`
- **Appium 执行链路**：测试脚本 → Appium Server → UiAutomator2 → 设备（HTTP 命令交互）
- **capabilities**：`platformName / deviceName / appPackage / appActivity / automationName`
- **环境版本矩阵**：Node 16 → Appium **2.19.0** → uiautomator2 **4.2.1**；
 装最新版 Appium（3.x）在 Node 16 上启动即崩，driver 5.x 则要求 Node ≥ 20.19
- **测试隔离**：`driver` fixture 建会话前 `adb shell pm clear <包名>` 清空 App 数据
 （可用 `--keep-app-data` 跳过），再配合每条用例显式拉起登录页，
 避免上一条用例花掉的余额、残留的提示文案影响下一条（真实排障过程见上面「踩坑记录」）
- **为什么要校验控件契约**：不连设备就能发现「用例改了 id、App 没改」这类低级事故
- **CI 里为什么不直接跑真机**：模拟器在 GitHub 托管 runner 上成本高（需 KVM + 较长启动时间），
 所以默认只跑静态校验与免设备用例；真机回归放自建环境或云真机，用仓库变量开关

## CI 说明

`.github/workflows/ci.yml` 有两个 job：

| job | 触发条件 | 做什么 |
|---|---|---|
| `static-check` | 每次 push / PR | py_compile 语法检查、布局与控件 id 契约校验、manifest 校验、用例收集（`--collect-only`）、免设备用例（`--no-device`） |
| `device-tests` | 仓库 Variable `ENABLE_DEVICE_CI=true` | 编译 APK（`./gradlew assembleDebug`，wrapper 已在仓库里）→ 启动 Android 模拟器 → 起 Appium → `pytest -m smoke` → 上传 HTML 报告 |

`device-tests` 默认关闭，是因为它耗时长且需要 runner 支持 KVM。想开启：仓库
`Settings → Secrets and variables → Actions → Variables` 新建 `ENABLE_DEVICE_CI` = `true`。

> **如实说明**：`device-tests` **还没有在 GitHub runner 上真正开启执行过**。
> 卡点不在 Gradle Wrapper（已就位并带 git 执行位，本机已构建成功），也不在版本管理
> （workflow 里已锁死 `appium@2.19.0` + `uiautomator2@4.2.1`），而在于：
> ① 云端模拟器是 `api-level: 30`，与本地验证过的 Android 9 / API 28 不同，需重新核对控件与行为；
> ② runner 上跑 Android 模拟器需要 KVM，托管 runner 不一定满足。
> **本地等价流程已经跑通全量 18 条**，这是当前最硬的证据。

## 可扩展方向

- **让云端真机 job 也真跑起来**：把云端模拟器 API 对齐到已验证的 Android 9，确认 KVM 可用后打开 `ENABLE_DEVICE_CI`
- **多设备并行 + 真机（ARM）验证**：用 `pytest-xdist` 分片到多台模拟器；
  再借一台 ARM 真机补上「只在 x86_64 模拟器验证过」的缺口
- **测试平台雏形**：用一个网页展示「用例列表 + 最近一次执行结果 + 报告链接」，
 后端读 `pytest-json-report` 产出的结果文件，先做最小闭环再做趋势图
- **弱网专项**：用 Charles 做限速 / 丢包，补「支付请求超时后是否重复提交」「弱网下是否给出明确提示」用例
- **登录态管理**：覆盖 token 过期、多端登录互踢、退出登录后返回键不能回到已登录页面
- **支付异常分支补齐**：服务端回调重复 / 金额篡改 / 掉单补偿（可先在 demo-app 里造出这些分支）
- **接入 Allure + 失败自动通知**：报告归档到 GitHub Pages，失败时推送到企业微信 / 钉钉

## 相关文档

- 部署到 GitHub 的完整教程见上一级目录：`../教程-项目2-移动端自动化测试-部署到运行到GitHub.md`
- 逐行代码讲解见：`代码逐行讲解.md`
