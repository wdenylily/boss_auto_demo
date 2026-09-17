# core/api_client.py
# ────────────────────────────────────────────────────────────
# 接口客户端封装
# 设计目标：
#   1. 统一：基础 URL、鉴权、超时、重试、日志、报告
#   2. 易用：client.get/post/put/delete 返回统一响应对象
#   3. 可测：支持 Mock、录制回放、契约测试扩展
# ────────────────────────────────────────────────────────────

import requests                                    # HTTP 库标准选择
from requests.adapters import HTTPAdapter          # 连接适配器（用于配置重试）
from urllib3.util.retry import Retry               # urllib3 重试策略
from typing import Optional, Dict, Any             # 类型提示
import logging                                     # 标准日志
from core.config_loader import config              # 配置单例


# 配置日志器
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# 1. 统一响应包装类：把 requests.Response 包装成「断言友好」的对象
# ═══════════════════════════════════════════════════════════
class APIResponse:
    """
    封装 requests.Response，提供：
    - .json / .text 直接取值
    - 链式断言方法：assert_status()、assert_json_path()、assert_json_contains()
    """
    
    def __init__(self, resp: requests.Response):
        self._resp = resp                      # 原始响应对象
        self.status_code = resp.status_code    # 状态码
        self.headers = resp.headers            # 响应头
        self._json = None                      # 缓存解析后的 JSON
        self._text = resp.text                 # 原始文本

    @property
    def json(self) -> dict:
        """懒加载 JSON：第一次调用时解析，后续直接返回缓存"""
        if self._json is None:
            try:
                self._json = self._resp.json()
            except Exception:
                self._json = {}                # 非 JSON 响应返回空字典，避免报错
        return self._json

    @property
    def text(self) -> str:
        return self._text

    # ─── 断言助手：返回 self 支持链式调用 ───
    def assert_status(self, expected: int) -> "APIResponse":
        """断言状态码"""
        assert self.status_code == expected, (
            f"状态码不符: 期望 {expected}, 实际 {self.status_code}, "
            f"响应体: {self.text[:200]}"
        )
        return self

    def assert_json_path(self, path: str, expected) -> "APIResponse":
        """
        断言 JSON 指定路径的值
        path 格式：'data.user.name'、'items[0].id'
        """
        actual = self.json
        for key in path.split("."):
            if isinstance(actual, dict):
                actual = actual.get(key)
            elif isinstance(actual, list) and key.isdigit():
                actual = actual[int(key)]
            else:
                actual = None
                break
        assert actual == expected, (
            f"JSON 路径 {path} 不符: 期望 {expected}, 实际 {actual}"
        )
        return self

    def assert_json_contains(self, key: str, expected_value) -> "APIResponse":
        """断言 JSON 包含某键且值相等"""
        assert key in self.json, f"响应缺少字段 {key}"
        assert self.json[key] == expected_value, f"字段 {key} 值不符"
        return self


# ═══════════════════════════════════════════════════════════
# 2. 接口客户端主类
# ═══════════════════════════════════════════════════════════
class APIClient:
    """
    核心能力：
    - 连接池复用（requests.Session）
    - 统一重试策略（幂等接口自动重试 5xx）
    - 统一鉴权（Bearer Token）
    - 统一日志（请求/响应/耗时）
    - 统一超时控制
    """
    
    def __init__(self, base_url: str = None, timeout: int = 10):
        # 基础 URL：优先用传入参数，其次读配置，最后兜底
        self.base_url = base_url or getattr(config, "api_base_url", "https://api.example.com")
        self.timeout = timeout                 # 请求超时秒数
        
        # ─── 创建 Session：连接池复用、Cookie 自动管理、Headers 统一注入 ───
        self.session = requests.Session()
        self._setup_retry()                    # 配置重试策略
        self._default_headers = {              # 默认请求头
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.token = None                      # 存储登录后的 token

    def _setup_retry(self):
        """
        配置重试策略：
        - 总重试 3 次
        - 指数退避：0.5s, 1s, 1.5s...
        - 只重试 5xx 服务端错误
        - 只重试幂等方法（GET/HEAD/OPTIONS/PUT/DELETE），POST 不重试（防重复下单）
        """
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "PUT", "DELETE"],
            raise_on_status=False,             # 不抛异常，让业务代码处理状态码
        )
        adapter = HTTPAdapter(max_retries=retry)
        # 为 http/https 都挂载适配器
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def set_auth_token(self, token: str):
        """设置 Bearer Token，后续所有请求自动带上 Authorization 头"""
        self.token = token
        self._default_headers["Authorization"] = f"Bearer {token}"

    def clear_auth_token(self):
        """清除 Token（登出场景）"""
        self.token = None
        self._default_headers.pop("Authorization", None)

    # ═══════════════════════════════════════════════════════════
    # 3. 核心请求方法（内部统一入口）
    # ═══════════════════════════════════════════════════════════
    def _request(self, method: str, path: str, **kwargs) -> APIResponse:
        """
        统一请求入口，所有 get/post/put/delete 最终都走这里
        参数透传给 requests.Session.request
        返回：APIResponse 统一包装对象
        """
        # 拼接完整 URL：去除首尾斜杠避免双斜杠
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        
        # 合并请求头：默认头 + 调用方传入的头
        headers = {**self._default_headers, **kwargs.pop("headers", {})}
        
        # 记录请求日志
        logger.info(f"🌐 {method} {url}")
        if "json" in kwargs:
            logger.debug(f"   Request Body: {kwargs['json']}")
        
        # 发起请求
        resp = self.session.request(
            method, url, headers=headers, timeout=self.timeout, **kwargs
        )
        
        # 包装响应
        api_resp = APIResponse(resp)
        
        # 记录响应日志
        logger.info(f"   ← {resp.status_code} ({resp.elapsed.total_seconds():.2f}s)")
        if resp.status_code >= 400:
            logger.warning(f"   Response: {resp.text[:500]}")
        
        return api_resp

    # ═══════════════════════════════════════════════════════════
    # 4. 便捷方法：语义化调用
    # ═══════════════════════════════════════════════════════════
    def get(self, path: str, params: Dict = None, **kwargs) -> APIResponse:
        """GET 请求：查询、获取列表、获取详情"""
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path: str, json: Dict = None, data: Dict = None, **kwargs) -> APIResponse:
        """POST 请求：创建资源、登录、提交表单"""
        return self._request("POST", path, json=json, data=data, **kwargs)

    def put(self, path: str, json: Dict = None, **kwargs) -> APIResponse:
        """PUT 请求：全量更新资源（幂等）"""
        return self._request("PUT", path, json=json, **kwargs)

    def patch(self, path: str, json: Dict = None, **kwargs) -> APIResponse:
        """PATCH 请求：部分更新资源"""
        return self._request("PATCH", path, json=json, **kwargs)

    def delete(self, path: str, **kwargs) -> APIResponse:
        """DELETE 请求：删除资源（幂等）"""
        return self._request("DELETE", path, **kwargs)


# ═══════════════════════════════════════════════════════════
# 5. 模块级单例：大多数场景直接 import 即用
# ═══════════════════════════════════════════════════════════
api_client = APIClient()
