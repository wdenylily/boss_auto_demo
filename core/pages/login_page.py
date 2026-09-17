# core/pages/login_page.py  # 登录页面对象文件路径。
"""登录页面对象。

技术栈：Python、Playwright 同步 API，以及 pytest（通常由测试用例调用本对象）。
设计思路：采用 Page Object Model（POM），集中管理定位器、页面操作和状态查询，
让测试用例只关注业务流程与断言，降低页面结构变化带来的维护成本。
"""
from playwright.sync_api import Page  # 导入 Playwright 页面类型，用于浏览器页面操作和类型标注。


class LoginPage:
    """封装登录页元素、登录动作及登录结果查询的页面对象。"""

    # === 选择器常量：集中管理，避免在测试用例中重复书写定位器。 ===
    USERNAME_INPUT = '[data-test="username"]'  # 用户名输入框的 data-test 定位器。
    PASSWORD_INPUT = '[data-test="password"]'  # 密码输入框的 data-test 定位器。
    LOGIN_BUTTON = '[data-test="login-button"]'  # 登录按钮的 data-test 定位器。
    ERROR_TEXT = '[data-test="error"]'  # 登录失败错误标题的 CSS 定位器。

    def __init__(self, page: Page):
        """接收并保存 Playwright 页面实例，供所有页面操作复用。"""
        self.page = page  # 保存当前浏览器标签页对象。

    # === 页面级操作 ===
    def goto(self, base_url: str):
        """打开登录页，并等待用户名输入框可见，确保页面已准备好交互。"""
        self.page.goto(base_url)  # 导航到测试环境的登录地址。
        self.page.locator(self.USERNAME_INPUT).wait_for(state="visible")  # 等待关键元素可见，减少异步加载导致的不稳定。

    # === 业务动作 ===
    def login(self, username: str, password: str):
        """填写用户名和密码并提交登录表单，封装完整登录业务流程。"""
        self.page.locator(self.USERNAME_INPUT).fill(username)  # 清空并填写用户名。
        self.page.locator(self.PASSWORD_INPUT).fill(password)  # 清空并填写密码。
        self.page.locator(self.LOGIN_BUTTON).click()  # 点击登录按钮，触发登录请求。

    def login_with_user_obj(self, user_obj):
        """从用户对象读取凭据并复用统一登录方法，适配测试数据对象或 fixture。"""
        self.login(user_obj.username, user_obj.password)  # 将用户对象属性传入登录流程。

    # === 状态查询（供测试断言）===
    def get_error_text(self) -> str:
        """读取登录失败提示文本，供测试用例进行断言。"""
        return self.page.locator(self.ERROR_TEXT).inner_text()  # 返回错误提示元素的可见文本。

    def is_logged_in(self) -> bool:
        """通过当前 URL 是否进入库存页判断登录是否成功。"""
        return self.page.url.endswith("/inventory.html")  # 匹配成功后的目标路径并返回布尔结果。