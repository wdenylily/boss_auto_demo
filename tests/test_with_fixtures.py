# tests/test_with_fixtures.py
# ────────────────────────────────────────────────────────────
# 第 5 步：使用 Fixture 的测试用例
# 对比 test_data_driven.py：没有任何启动浏览器、新建页面、登录代码
# ────────────────────────────────────────────────────────────

import pytest
from core.pages.login_page import LoginPage
from core.config_loader import config


def test_login_with_page_fixture(page):
    """
    直接注入 page fixture：自动获得干净的页面、自动失败截图、自动清理
    """
    login_page = LoginPage(page)
    login_page.goto(config.base_url)
    login_page.login_with_user_obj(config.users.standard)
    assert login_page.is_logged_in()


def test_login_locked_with_page_fixture(page):
    """
    同一个 page fixture，跑另一个场景
    """
    login_page = LoginPage(page)
    login_page.goto(config.base_url)
    login_page.login_with_user_obj(config.users.locked)
    assert "locked out" in login_page.get_error_text().lower()


def test_search_after_login(logged_in_page):
    """
    直接注入 logged_in_page fixture：跳过登录，直接在 inventory 页开始测试
    这就是「测试数据/状态复用」的典型场景
    """
    # logged_in_page 已经在 inventory 页
    assert logged_in_page.url.endswith("/inventory.html")
    # 这里可以继续写：搜索商品、加购、结账...
    print("✅ 复用登录态，直接测试后续业务")


# 数据驱动版本也可以用 fixture 改造（后续步骤演示）
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
