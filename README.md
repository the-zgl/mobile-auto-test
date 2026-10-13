# 移动端自动化测试框架（Appium + pytest + CI）

一个 **移动端测试开发** 方向的实践项目：一套按 **Page Object Model** 分层的 Android 自动化测试框架，
覆盖「**账号登录**」与「**购买 / 支付**」两条核心业务链路，自带被测 App，接入 **GitHub Actions** 持续集成。

> 目标：克隆下来就能真实跑通的测试工程，而不是只能看的示例代码。
>
> **当前状态（本机实测，非设想）**：已在 **Android 9（API 28）/ x86_64 模拟器 `emulator-5554`** 上
> **全量跑通 18 条用例 —— `18 passed in 136.45s (0:02:16)`**，HTML 报告生成在 `reports/report.html`；
> `gradlew assembleDebug` **BUILD SUCCESSFUL**，APK 约 **3.02 MB**，`adb install -r` 返回 **Success**。
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

## 环境准备（本机实测清单：很多东西已经有了，别重复装）

| 组件 | 本机状态 | 命令/路径 |
|---|---|---|
| Python | ✅ 已装 3.12 | `pip install -r requirements.txt` |
| **JDK 17** | ✅ **已有，不需要下载** | `D:\eclipse\plugins\org.eclipse.justj.openjdk.hotspot.jre.full.win32.x86_64_17.0.9.v20231028-0858\jre`（Temurin 17.0.9）；另有 IntelliJ JBR 17.0.12 在 `D:\Program Files\JetBrains\IntelliJ IDEA 2024.1.7\jbr` |
| **Android SDK** | ✅ **已有** | `D:\Users\<你的用户名>\AppData\Local`（含 `platforms/android-34`、`build-tools/34.0.0`、`platform-tools`、`emulator`） |
| **模拟器** | ✅ **已有并正在运行** | `emulator-5554` / `emulator-5556`，**都是 Android 9 / API 28 / x86_64** |
| **Gradle Wrapper** | ✅ **仓库已含 8.7** | `demo-app/gradlew`、`gradlew.bat`、`gradle/wrapper/`；**无需生成** |
| Node.js | ✅ 已装，但只有 **v16.15.0** | 这个版本决定了 Appium 必须锁 2.x |
| Appium Server + UiAutomator2 | ❌ 未装 | 见下面第 3 条（版本必须锁死） |

**1. Python 依赖**

```powershell
python --version
pip install -r requirements.txt
```

**2. JDK 17 + Android SDK（都已存在，只需设环境变量）**

```powershell
# JDK 17：本机已有，别去官网下载
$env:JAVA_HOME = "D:\eclipse\plugins\org.eclipse.justj.openjdk.hotspot.jre.full.win32.x86_64_17.0.9.v20231028-0858\jre"

# Android SDK：本机已有（注意路径末尾不是 \Android\Sdk）
$env:ANDROID_HOME = "D:\Users\<你的用户名>\AppData\Local"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME

# 先证明目录真的存在，再谈构建（本机原有 JAVA_HOME 指向不存在的 D:\java\jdk-17.0.9，是个坏配置）
Test-Path "$env:JAVA_HOME\bin\java.exe" # True
Test-Path "$env:ANDROID_HOME\platform-tools\adb.exe" # True
```

**3. Appium Server 2.19.0 + UiAutomator2 4.2.1（版本必须锁死，别装最新版）**

```powershell
npm install -g appium@2.19.0
appium driver install uiautomator2@4.2.1
```

> **为什么不能直接装最新版**（本机实测）：
> - 直接 `npm install -g appium` 会装到 **3.8.0**，在本机 **Node 16.15.0** 上启动即崩：
> `TypeError: (0 , U.tracingChannel) is not a function`。
> - `appium-uiautomator2-driver` **5.0.0 及以上要求 Node ≥ 20.19**，所以只能锁 **4.2.1**。
> - 结论：**Node 16.15.0 → Appium 2.19.0 → uiautomator2 4.2.1**，三者是配套的。

**4. 启动 Appium 时必须带上 `ANDROID_HOME`**（否则连设备会失败）

```powershell
$env:ANDROID_HOME = "D:\Users\<你的用户名>\AppData\Local"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
appium
```

> 变量必须和 `appium` 命令在**同一个 PowerShell 窗口**里设置。
> 否则连设备时会报
> `Neither ANDROID_HOME nor ANDROID_SDK_ROOT environment variable was exported`。
> 这两条也已写进 `conftest.py` 连接失败时的排查清单（第 5 条）。

**5. 确认设备在线**

```powershell
adb devices # 必须能看到一台 device 状态的设备（本机为 emulator-5554）
```

> **已在模拟器上实测通过**：全部 18 条用例在 Android 9（API 28）/ x86_64 模拟器上跑绿。
> **唯一未验证项：没有在真机（ARM）上跑过** —— 真机的 `adb` 连接、性能与 x86_64 模拟器不同，
> 所以本文档对 App 行为的描述都基于**模拟器实跑观测 + 源码逻辑**，不包含 ARM 真机结论。

## 部署与运行（4 步，命令均为本机实测可跑通）

```powershell
# 1) 编译并安装被测 App（在 demo-app 目录；wrapper 已在仓库里，直接用）
cd demo-app
$env:JAVA_HOME = "D:\eclipse\plugins\org.eclipse.justj.openjdk.hotspot.jre.full.win32.x86_64_17.0.9.v20231028-0858\jre"
$env:ANDROID_HOME = "D:\Users\<你的用户名>\AppData\Local"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
.\gradlew assembleDebug # 本机实测：BUILD SUCCESSFUL，产物约 3.02 MB
adb install -r app\build\outputs\apk\debug\app-debug.apk # 本机实测：Success

# 2) 启动 Appium 服务（新开一个窗口；必须带上 ANDROID_HOME）
$env:ANDROID_HOME = "D:\Users\<你的用户名>\AppData\Local"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
appium

# 3) 回到框架目录，确认设备信息与配置一致
cd ..
notepad config\config.yaml # deviceName=emulator-5554、platformVersion="9"（Android 9）

# 4) 跑用例
pytest -m smoke # 只跑冒烟（2 条）
pytest # 全量 18 条（本机实测 18 passed in 136.45s）
pytest --html=reports/report.html --self-contained-html # 带 HTML 报告
```

### 不连设备也能验证

```powershell
pytest --collect-only -q # 应输出 18 tests collected
pytest --no-device -q # 应输出 6 passed, 12 skipped
```

> **三个数字的口径，别搞混**：
> - 总共 **18 条**用例；
> - 其中 **14 条需要设备**（账号 6 + 支付 6 + `smoke` 标记 2）、**4 条免设备**；
> - `--no-device` 会跳过**依赖 `driver` fixture 的 12 条** → 所以显示 `6 passed, 12 skipped`（6 + 12 = 18）。
>
> 「需要设备 14 条」和「`--no-device` skip 12 条」是两套口径，**都能对上 18**，不是矛盾。

### 用例间状态隔离（`--keep-app-data`）

`conftest.py` 的 `driver` fixture 在**建立 Appium 会话之前**会执行
`adb shell pm clear com.daping.demoshop`，把 App 数据（余额、残留提示文案）清干净，
保证每条用例都从同一个确定起点开始。

```powershell
pytest --keep-app-data # 想观察「连续状态」时，用这个参数跳过清理
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

## 核心知识点

- **Page Object Model**：元素定位与业务流程分离，App 改版只改一处；用属性（`@property`）把
 「余额：1000 分」解析成整数，断言才能做数值比较
- **fixture 作用域**：`driver` 用 `function` 保证用例隔离；`config`/`caps` 用 `session` 避免重复读盘
- **显式等待 vs 隐式等待**：隐式等待对「元素已存在但不可见」无效，所以统一用 `WebDriverWait`
- **Appium 执行链路**：测试脚本 → Appium Server → UiAutomator2 → 设备（HTTP 命令交互）
- **capabilities**：`platformName / deviceName / appPackage / appActivity / automationName`
- **环境版本矩阵**：Node 16.15.0 → Appium **2.19.0** → uiautomator2 **4.2.1**；
 装最新版 Appium（3.x）在本机 Node 上启动即崩，driver 5.x 则要求 Node ≥ 20.19
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
> 卡点不在 Gradle Wrapper（已就位，本机已构建成功），而在两处：
> ① workflow 里是 `npm install -g appium`，没锁版本，在 runner 的新 Node 上会装到 3.x，
> 与本机验证过的组合（Node 16.15.0 + Appium 2.19.0 + uiautomator2 4.2.1）不一致；
> ② 云端模拟器（`api-level: 30`）与本机验证过的 Android 9 / API 28 不同。
> **本机等价流程已经跑通全量 18 条**，这是当前最硬的证据。

## 可扩展方向

- **让云端真机 job 也真跑起来**：把 CI 里的 Appium 版本锁死并统一模拟器 API，再打开 `ENABLE_DEVICE_CI`
- **多设备并行 + 真机（ARM）验证**：本机已有 `emulator-5554` / `emulator-5556`，
 可用 `pytest-xdist` 分片；再借一台 ARM 真机补上「只在 x86_64 模拟器验证过」的缺口
- **测试平台雏形**：用一个网页展示「用例列表 + 最近一次执行结果 + 报告链接」，
 后端读 `pytest-json-report` 产出的结果文件，先做最小闭环再做趋势图
- **弱网专项**：用 Charles 做限速 / 丢包，补「支付请求超时后是否重复提交」「弱网下是否给出明确提示」用例
- **登录态管理**：覆盖 token 过期、多端登录互踢、退出登录后返回键不能回到已登录页面
- **支付异常分支补齐**：服务端回调重复 / 金额篡改 / 掉单补偿（可先在 demo-app 里造出这些分支）
- **接入 Allure + 失败自动通知**：报告归档到 GitHub Pages，失败时推送到企业微信 / 钉钉

## 相关文档

- 部署到 GitHub 的完整教程见上一级目录：`../教程-项目2-移动端自动化测试-部署到运行到GitHub.md`
- 逐行代码讲解见：`代码逐行讲解.md`
