# tests/test_data_driven.py
# ────────────────────────────────────────────────────────────
# 第 4 步：数据驱动测试（修复版）
# 核心修复：config.users 是 SimpleNamespace，必须用 getattr 动态取属性
# 使用 page fixture 替代手动 sync_playwright()
# ────────────────────────────────────────────────────────────

import pytest                          # pytest 测试框架核心
import yaml                            # PyYAML：解析 YAML 文件
from pathlib import Path               # pathlib：面向对象的路径操作（跨平台安全）
from core.config_loader import config  # 我们的配置单例
from core.pages.login_page import LoginPage      # 我们的 Page Object


# ═══════════════════════════════════════════════════════════
# 1. 读取测试数据（模块加载时执行 1 次，不在每个测试里重复读）
# ═══════════════════════════════════════════════════════════
TESTDATA_PATH = Path(__file__).parent.parent / "config" / "testdata" / "login_cases.yaml"

with open(TESTDATA_PATH, encoding="utf-8") as f:
    LOGIN_CASES = yaml.safe_load(f)   # 结果：[{case_id:..., name:..., ...}, ...]


# ═══════════════════════════════════════════════════════════
# 2. 参数化装饰器：把列表里的每个字典「展开」成独立测试用例
# ═══════════════════════════════════════════════════════════
@pytest.mark.parametrize("case", LOGIN_CASES, ids=lambda c: f"{c['case_id']}_{c['name']}")
def test_login_data_driven(page, case):
    """
    单一测试函数，跑所有登录场景
    参数 case：字典，包含当前场景的所有字段
    使用 page fixture：自动获得干净的页面、自动失败截图、自动清理
    """
    # ─── 实例化 Page Object ───
    login_page = LoginPage(page)
    login_page.goto(config.base_url)

    # ─── 从 case 字典提取参数，支持默认值回退 ───
    user_key = case.get("user_key", "standard")                    # 默认 standard

    # 🔧 修复点：config.users 是 SimpleNamespace，用 getattr 动态取属性
    # getattr(对象, "属性名字符串") 等价于 对象.属性名
    # 先拿到 user 对象（如 config.users.standard），再取 username/password
    user_obj = getattr(config.users, user_key)          # 拿到 standard/locked/problem 对象
    username = case.get("username", user_obj.username)  # 取用户名，允许 case 覆盖
    password = case.get("password", user_obj.password)  # 取密码，允许 case 覆盖

    # ─── 执行登录动作 ───
    login_page.login(username, password)

    # ─── 根据期望结果断言 ───
    if case["expect_success"]:
        assert login_page.is_logged_in(), f"[{case['case_id']}] 预期成功但失败了"
    else:
        error_text = login_page.get_error_text().lower()
        expected = case["expect_error_contains"].lower()
        assert expected in error_text, (
            f"[{case['case_id']}] 报错文案不符："
            f"实际={error_text}，期望包含={expected}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])