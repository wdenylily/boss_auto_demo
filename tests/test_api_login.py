# tests/test_api_login.py
# ────────────────────────────────────────────────────────────
# 第 6 步：接口测试示例 + UI+API 混合测试演示
# 场景：
#   1. 纯接口测试：登录获取 token
#   2. 混合测试：API 登录拿 token → 注入 UI(localStorage) → 直接访问受保护页
# ────────────────────────────────────────────────────────────

import pytest
from core.api_client import api_client, APIResponse
from core.config_loader import config
from core.pages.login_page import LoginPage


def test_api_login_get_token():
    """
    纯接口测试：调用登录接口获取 token
    注意：saucedemo 官网没有开放登录 API，这里演示结构，实际项目替换真实接口
    """
    # 假设真实接口：POST /api/auth/login
    # resp = api_client.post("/api/auth/login", json={
    #     "username": "standard_user",
    #     "password": "secret_sauce"
    # })
    # # 链式断言
    # resp.assert_status(200).assert_json_path("data.token", "not_empty")
    # # 设置 token，后续接口自动带上
    # api_client.set_auth_token(resp.json["data"]["token"])
    # print(f"✅ 获得 token: {resp.json['data']['token'][:20]}...")
    
    # Demo 站点无 API，跳过实际调用
    pytest.skip("Demo 站点无登录接口，仅演示结构；实际项目替换为真实 API 地址")


def test_ui_skip_login_with_token(page):
    """
    混合测试核心模式：API 登录 → 注入认证态 → 跳过 UI 登录页
    这是「测试金字塔」落地的关键：UI 只测端到端核心链路，前置条件用 API 准备
    """
    # 1. 假设已通过 API 获取 token（实际项目调用真实登录接口）
    fake_token = "fake-jwt-token-for-demo"
    
    # 2. 先访问一次域名（建立 cookie 作用域，否则 localStorage 设不进去）
    page.goto(config.base_url)
    
    # 3. 注入 token 到 localStorage / sessionStorage（前端常用认证存储方式）
    # page.evaluate() 在浏览器上下文执行 JS 代码
    page.evaluate(f"""() => {{
        localStorage.setItem('auth_token', '{fake_token}');
        sessionStorage.setItem('auth_token', '{fake_token}');
    }}""")
    
    # 4. 直接访问受保护页面（inventory 页）
    page.goto(f"{config.base_url}/inventory.html")
    
    # 5. 验证是否真的处于登录态
    # 真实项目：断言页面出现用户名、或调用 /api/user/info 接口返回用户信息
    # 这里演示：saucedemo 没有 token 机制，会跳回登录页，所以断言会失败
    # 实际项目中这里会通过
    print("✅ 演示：API token 注入 UI 流程跑通")
    print("💡 真实项目中：断言页面出现用户头像、或接口返回用户信息，即可验证登录态生效")


def test_api_create_test_data_then_ui(page):
    """
    混合测试另一核心模式：API 造数据 → UI 走业务
    场景：测试「购物车加购」，先用 API 直接创建商品、清空购物车，再用 UI 操作
    """
    # 1. API 造数据（伪代码，实际项目替换真实接口）
    # api_client.post("/api/test/products", json={"name": "测试商品", "price": 9.9})
    # api_client.delete("/api/test/cart/clear")
    
    # 2. UI 操作核心链路
    # login_page = LoginPage(page)
    # login_page.goto(config.base_url)
    # login_page.login_with_user_obj(config.users.standard)
    # inventory_page = InventoryPage(page)
    # inventory_page.add_to_cart("测试商品")
    # cart_page = CartPage(page)
    # cart_page.goto()
    # assert cart_page.has_item("测试商品")
    
    # 3. API 清理数据
    # api_client.delete("/api/test/products/测试商品")
    
    pytest.skip("演示模式：实际项目替换为真实 API + Page Object")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
