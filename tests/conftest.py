# tests/conftest.py
# ────────────────────────────────────────────────────────────
# conftest.py：pytest 自动发现的全局配置文件
# 作用：
#   1. 定义共享 Fixture（浏览器、上下文、页面、登录态）
#   2. 定义钩子函数（失败自动截图、记录日志）
#   3. 注册自定义命令行参数（如 --env 切环境）
# 约定：文件名必须叫 conftest.py，放在 tests/ 目录下
# ────────────────────────────────────────────────────────────

import pytest                                    # pytest 核心
from playwright.sync_api import sync_playwright  # Playwright 同步 API
from core.config_loader import config            # 配置单例
import time                                      # 时间戳用于截图命名


# ═══════════════════════════════════════════════════════════
# 1. 会话级浏览器 Fixture：整个测试运行期间只启动 1 次浏览器进程
# ═══════════════════════════════════════════════════════════
# scope="session"：所有测试函数共享这一个 browser 对象
# 优点：启动快、省内存；缺点：测试间需靠 Context 隔离状态
@pytest.fixture(scope="session")
def browser():
    """
    返回：playwright Browser 对象
    生命周期：测试开始前 setup 启动 → yield 给测试用 → 测试结束后 teardown 关闭
    """
    with sync_playwright() as p:
        # 从配置动态获取浏览器类型：p.chromium / p.firefox / p.webkit
        browser_type = getattr(p, config.browser)
        # 启动参数统一从配置读取
        launch_args = {
            "headless": config.headless,      # True=无头，False=有头
            "slow_mo": config.slow_mo,        # 每步延迟毫秒数，调试用
        }
        browser = browser_type.launch(**launch_args)
        yield browser          # 👈 把 browser 交给下游 fixture / 测试函数使用
        browser.close()        # 👈 所有测试跑完后自动关闭浏览器进程


# ═══════════════════════════════════════════════════════════
# 2. 函数级上下文 Fixture：每个测试函数独享一个 BrowserContext
# ═══════════════════════════════════════════════════════════
# BrowserContext = 隔离的浏览器上下文
#   - 独立 cookies / localStorage / sessionStorage / 缓存
#   - 相当于「无痕窗口」，但比无痕窗口轻量、启动更快
#   - 不同测试函数用不同 Context → 彻底隔离登录态、购物车等状态
@pytest.fixture(scope="function")
def context(browser):
    """
    参数 browser：自动注入上一级 fixture 返回的 Browser 对象
    返回：BrowserContext 对象
    """
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 720},  # 固定视口大小，避免响应式布局导致定位失败
        locale="zh-CN",                           # 语言/地区
        timezone_id="Asia/Shanghai",              # 时区
        # 可选：录制视频
        # record_video_dir="reports/videos/",
    )
    yield ctx
    ctx.close()   # 测试结束自动关闭 Context，释放资源


# ═══════════════════════════════════════════════════════════
# 3. 函数级页面 Fixture：每个测试函数独享一个 Page（标签页）
# ═══════════════════════════════════════════════════════════
# 这是测试函数最常直接注入的 fixture
@pytest.fixture(scope="function")
def page(context):
    """
    参数 context：自动注入上一级 fixture 返回的 Context
    返回：Page 对象
    附带能力：
      - 失败自动截图（在 teardown 里）
      - 控制台报错监听
      - 页面 JS 错误监听
    """
    pg = context.new_page()
    
    # ─── 监听控制台报错（只打印 error 级别，避免刷屏）───
    pg.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}") if msg.type == "error" else None)
    # ─── 监听页面 JS 异常 ───
    pg.on("pageerror", lambda exc: print(f"[PAGE ERROR] {exc}"))
    
    yield pg
    
    # ─── Teardown：测试结束自动执行（无论通过/失败）───
    # 截一张「结束时」的全页截图，方便事后复盘
    try:
        # 生成文件名：时间戳 + URL 片段（去掉非法字符）
        # GitHub Actions upload-artifact 不允许文件名含 : " < > | * ? \r \n
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        _raw_url = pg.url.replace("https://", "").replace("http://", "").replace("/", "_")
        for _bad in (":", '"', "<", ">", "|", "*", "?", "\r", "\n"):
            _raw_url = _raw_url.replace(_bad, "_")
        safe_url = _raw_url[:80]
        shot_path = f"reports/last_{safe_url}_{timestamp}.png"
        pg.screenshot(path=shot_path, full_page=True)
        print(f"📸 运行末态截图: {shot_path}")
    except Exception:
        # 截图失败不影响测试结果，静默忽略
        pass
    pg.close()   # 关闭页面


# ═══════════════════════════════════════════════════════════
# 4. 登录态 Fixture：前置登录，返回已登录的 Page
# ═══════════════════════════════════════════════════════════
# 适用场景：所有「需要登录后才能操作」的测试（搜索、投递、聊天、下单…）
@pytest.fixture(scope="function")
def logged_in_page(page):
    """
    参数 page：自动注入上面的 page fixture（干净的新页面）
    返回：已登录的 Page 对象（停在 inventory 页）
    """
    # 延迟导入，避免循环导入
    from core.pages.login_page import LoginPage
    
    login_page = LoginPage(page)
    login_page.goto(config.base_url)
    login_page.login_with_user_obj(config.users.standard)
    
    # 断言登录成功，失败直接抛错（pytest 会标记测试失败）
    assert login_page.is_logged_in(), "前置登录失败，后续测试无意义"
    
    yield page
    # Teardown：可选，如登出、清理测试数据


# ═══════════════════════════════════════════════════════════
# 5. 钩子：失败自动截图 + 打印关键信息
# ═══════════════════════════════════════════════════════════
# pytest_runtest_makereport 是 pytest 核心钩子
# 每个测试的 setup/call/teardown 三个阶段结束都会触发
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    item: 测试项对象（含名称、参数、fixture 等）
    call: 当前阶段 ("setup" / "call" / "teardown")
    """
    # 执行下一步，拿到结果对象
    outcome = yield
    rep = outcome.get_result()
    
    # 只处理「测试主体阶段」的失败
    if rep.when == "call" and rep.failed:
        # 从测试项的 fixture 缓存里拿到 page 对象
        page = item.funcargs.get("page")
        if page:
            # 生成失败截图文件名（清洗非法字符，artifact 上传不允许 : " < > | * ? 等）
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            _safe_name = item.name
            for _bad in (":", '"', "<", ">", "|", "*", "?", "\r", "\n"):
                _safe_name = _safe_name.replace(_bad, "_")
            shot_name = f"FAILED_{_safe_name}_{timestamp}.png"
            shot_path = f"reports/{shot_name}"
            try:
                page.screenshot(path=shot_path, full_page=True)
                print(f"\n📸 失败截图已保存: {shot_path}")
                # 如果后续集成 Allure，这里可以附件上传：
                # import allure
                # allure.attach.file(shot_path, name="failure_screenshot", attachment_type=allure.attachment_type.PNG)
            except Exception as e:
                print(f"截图失败: {e}")


# ═══════════════════════════════════════════════════════════
# 6. 命令行参数：支持 pytest --env=prod 动态切环境
# ═══════════════════════════════════════════════════════════
def pytest_addoption(parser):
    """注册自定义命令行参数"""
    parser.addoption(
        "--env",
        action="store",
        default="test",
        help="指定运行环境: test/stage/prod"
    )

@pytest.fixture(scope="session", autouse=True)
def switch_env(request):
    """
    autouse=True：无需测试显式请求，自动应用到所有测试
    作用：根据 --env 动态加载对应配置文件（实际项目会覆盖 config）
    """
    env = request.config.getoption("--env")
    print(f"\n🌍 当前运行环境: {env}")
    # 实际项目：这里加载 config/env.{env}.yaml 并合并到 config 对象
    # Demo 简化：只打印
