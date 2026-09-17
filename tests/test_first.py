# tests/test_first.py
# 这是测试文件的路径说明：这个脚本位于 tests 目录下，名字叫 test_first.py。
# 它是整个自动化测试项目中的第一个示例脚本，用来验证基本环境和工具是否能正常工作。
"""
第 1 步：最小可行脚本
目的：验证 Playwright + Pytest 能跑通
"""
# 这是模块级文档字符串（Docstring），用于描述这个文件的整体作用。
# 在 Python 中，三重双引号字符串通常放在文件顶部，说明这个脚本的功能和目标。
# 这里的意思是：这是“最小可行脚本”，目的是确认 Playwright 和 Pytest 能一起正常运行。

# 导入 pytest（用于断言等）
import pytest
from core.config_loader import config


# 定义一个测试函数，函数名必须以 test_ 开头，Pytest 会自动将它当作测试用例识别。
# 这里的 test_login_saucedemo 表示这个测试的作用：验证登录功能是否能成功。
def test_login_saucedemo(page):
    """
    测试目标：登录 saucedemo.com（公开测试电商站）
    流程：打开页 → 输入账号密码 → 点登录 → 断言跳转成功
    使用 page fixture：自动获得干净的页面、自动失败截图、自动清理
    """
    # 这是函数的说明文档字符串。
    # 它解释了这个测试的目标：访问 saucedemo.com 这个公开示例网站，执行登录操作。
    # 流程中也说明了基本步骤：打开页面、输入账号密码、点击登录、断言跳转成功。

    # 使用 page fixture 打开目标网页。
    # 这里访问的是 saucedemo.com 的登录页，这是一个常见的测试站点，适合练习自动化测试。
    page.goto(config.base_url)

    # 定位页面上用户名输入框，并填写账号。
    # [data-test="username"] 是这个网站用来标识用户名输入框的属性选择器。
    # fill() 方法表示输入文本内容，参数 "standard_user" 是该站点的标准账号。
    page.locator('[data-test="username"]').fill("standard_user")
    # 定位页面上密码输入框，并填写正确密码。
    # 这里的 "secret_sauce" 是标准用户对应的密码，通常用于该演示站点的登录验证。
    page.locator('[data-test="password"]').fill("secret_sauce")
    # 定位登录按钮并点击。
    # [data-test="login-button"] 是登录按钮的选择器，click() 表示执行鼠标点击动作。
    page.locator('[data-test="login-button"]').click()

    # 断言登录后的页面 URL 是否等于库存页地址。
    # 如果登录成功，页面通常会跳转到 https://www.saucedemo.com/inventory.html。
    # assert 是 Python 的断言语句，用来校验预期是否成立；如果不成立，测试会直接失败。
    assert page.url == f"{config.base_url}/inventory.html"

    # 打印一条成功信息，方便在控制台看到测试结果。
    # 这里是一个“人工确认”的输出，可以帮助开发者快速判断脚本是否跑通。
    print("✅ 第 1 步通过：登录测试跑通！")


# if __name__ == "__main__": 的含义是：只有当这个脚本被直接执行时，下面的代码才会运行。
# 如果这个文件被 pytest 作为测试文件导入，不会执行这里的代码。
# 这是 Python 常见的脚本入口写法，便于既能直接运行测试，又能被测试框架收集。
if __name__ == "__main__":
    # 直接手动调用测试函数，模拟“单独运行这个脚本”的行为。
    # 在命令行中执行 python test_first.py 时，就会触发这行代码。
    pytest.main([__file__, "-v", "-s"])