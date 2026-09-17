# tests/test_with_config.py：pytest 会发现并执行此测试文件。
"""
第 2 步：引入配置层

本文件的组织方式：pytest 负责发现 test_ 开头的测试函数并报告结果；
Playwright 负责驱动真实浏览器；config_loader 负责集中管理环境和账号配置，
从而将测试逻辑与测试数据解耦。每个用例都遵循“准备、执行、验证、清理”流程。
"""
# 导入 pytest（用于断言等）
import pytest
# 导入项目配置对象，避免在测试代码中硬编码地址、浏览器和账号。
from core.config_loader import config


def test_login_with_config(page):
    # pytest 将此函数识别为一个独立的测试用例。
    # 使用 page fixture：自动获得干净的页面、自动失败截图、自动清理

    # 访问被测系统登录页，完成测试前置准备。
    page.goto(config.base_url)
    # 从配置层读取标准用户，保持测试逻辑和测试数据分离。
    user = config.users.standard
    # 通过稳定的 data-test 属性定位用户名输入框并填写数据。
    page.locator('[data-test="username"]').fill(user.username)
    # 定位密码输入框并填写密码。
    page.locator('[data-test="password"]').fill(user.password)
    # 定位登录按钮并点击，执行被测功能。
    page.locator('[data-test="login-button"]').click()

    # 断言登录后的地址，验证标准用户成功进入库存页。
    assert page.url == f"{config.base_url}/inventory.html"
    # 输出辅助信息；测试是否通过由 assert 和 pytest 决定。
    print(f"✅ 使用配置 [{config.browser}] 登录通过！")


def test_login_locked_user(page):
    # 第二个独立用例，验证锁定用户登录失败的负向场景。

    # 打开登录页，完成测试前置准备。
    page.goto(config.base_url)
    # 从配置层读取锁定用户。
    user = config.users.locked
    # 填写锁定用户的用户名。
    page.locator('[data-test="username"]').fill(user.username)
    # 填写锁定用户的密码。
    page.locator('[data-test="password"]').fill(user.password)
    # 提交登录请求，触发系统的用户状态校验。
    page.locator('[data-test="login-button"]').click()

    # 定位页面上的错误提示元素。
    error_locator = page.locator('[data-test="error"]')
    # 断言错误文本包含预期内容，验证业务规则。
    assert "locked out" in error_locator.inner_text().lower()
    # 输出辅助信息；真正的结果仍由断言和测试框架判断。
    print("✅ 锁定用户登录失败，报错符合预期")


if __name__ == "__main__":
    # 直接运行本文件时手动执行用例；使用 pytest 时则由 pytest 自动收集。
    pytest.main([__file__, "-v", "-s"])