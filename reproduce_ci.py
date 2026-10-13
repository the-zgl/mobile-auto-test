# -*- coding: utf-8 -*-
"""在本地复现 GitHub Actions static-check job 的每一步。

用途：上传前确认 CI 会是绿的，而不是推上去才发现红了。
CI 定义见 .github/workflows/ci.yml 的 static-check job。
"""
import glob
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

results = []


def step(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if detail else ""))


def run(cmd, cwd=ROOT):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# ---- 1) Syntax check (py_compile) ----
files = ["conftest.py"] + sorted(glob.glob("pages/*.py")) + sorted(glob.glob("tests/*.py"))
code, out = run([PY, "-m", "py_compile"] + files)
step("py_compile 语法检查", code == 0, out.strip()[-200:] if code else f"{len(files)} 个文件")

# ---- 2) Validate Android layouts and id contract ----
layout_files = glob.glob("demo-app/app/src/main/res/layout/*.xml")
value_files = glob.glob("demo-app/app/src/main/res/values/*.xml")
ok = bool(layout_files)
merged = ""
declared = ""
try:
    for f in layout_files:
        merged += open(f, encoding="utf-8").read()
        ET.parse(f)
    for f in value_files:
        ET.parse(f)
        declared += open(f, encoding="utf-8").read()
except Exception as exc:
    ok = False
    merged = ""
missing = [i for i in ("username", "password", "login", "error", "tv_balance", "tv_pay_success", "btn_buy")
           if f'@+id/{i}"' not in merged]
for row_id in ("item_0", "item_1", "item_2", "item_3", "item_4"):
    if f'name="{row_id}"' not in declared and f'@+id/{row_id}"' not in merged:
        missing.append(row_id)
step("布局与 id 契约校验", ok and not missing,
     f"{len(layout_files)} 布局 / {len(value_files)} values" if ok and not missing else f"缺失 {missing}")

# ---- 3) Validate manifest (XML) ----
try:
    ET.parse("demo-app/app/src/main/AndroidManifest.xml")
    step("manifest XML 校验", True)
except Exception as exc:
    step("manifest XML 校验", False, str(exc))

# ---- 4) Collect tests ----
code, out = run([PY, "-m", "pytest", "--collect-only", "-q"])
collected = ""
for line in out.splitlines():
    if "test" in line and "collected" in line:
        collected = line.strip()
step("用例收集 (--collect-only)", code == 0, collected or out.strip()[-120:])

# ---- 5) Run device-free framework tests ----
code, out = run([PY, "-m", "pytest", "--no-device", "-q"])
summary = ""
for line in out.splitlines():
    if "passed" in line or "failed" in line:
        summary = line.strip()
step("免设备用例 (--no-device)", code == 0, summary or out.strip()[-120:])

# ---- 汇总 ----
print()
failed = [n for n, ok, _ in results if not ok]
print(f"共 {len(results)} 步，失败 {len(failed)} 步")
if failed:
    print("失败步骤:", failed)
    sys.exit(1)
print("static-check job 在本地全部通过 ✓  （推送到 GitHub 后这个 job 应该也是绿的）")
