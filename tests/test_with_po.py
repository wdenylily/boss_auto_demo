# tests/test_with_po.py：Page Object 模式下的登录自动化测试文件。
"""第 3 步：引入 Page Object；测试代码零选择器，只表达业务意图。"""  # 模块说明：使用 POM 分离测试逻辑与页面细节。
import pytest
from core.config_loader import config  # 导入配置对象，实现浏览器、环境和账号的配置驱动。
from core.pages.login_page import LoginPage  # 导入登录页对象，封装选择器和登录业务操作。


def test_login_success(page):  # 定义成功登录用例；pytest 会自动发现 test_ 开头的测试函数。
    # 使用 page fixture：自动获得干净的页面、自动失败截图、自动清理

    login_page = LoginPage(page)  # 注入 Page 实例，创建登录页 Page Object。
    login_page.goto(config.base_url)  # 访问配置中的应用地址。
    login_page.login_with_user_obj(config.users.standard)  # 使用标准用户对象执行封装后的登录流程。

    assert login_page.is_logged_in()  # 断言登录状态，验证正向业务结果。
    print("✅ PO 版本：标准用户登录通过")  # 输出本地运行时的成功提示。


def test_login_locked_user(page):  # 定义锁定用户用例，覆盖登录失败的负向场景。
    # 使用 page fixture：自动获得干净的页面、自动失败截图、自动清理

    login_page = LoginPage(page)  # 创建登录页对象，隐藏底层选择器细节。
    login_page.goto(config.base_url)  # 打开待测应用的登录页面。
    login_page.login_with_user_obj(config.users.locked)  # 使用锁定账号执行登录操作。

    error_text = login_page.get_error_text().lower()  # 获取错误提示并统一转换为小写。
    assert "locked out" in error_text  # 断言提示包含预期关键词，验证异常业务逻辑。
    print("✅ PO 版本：锁定用户报错符合预期")  # 输出负向测试通过提示。


if __name__ == "__main__":  # 判断是否由 Python 直接执行本文件。
    pytest.main([__file__, "-v", "-s"])