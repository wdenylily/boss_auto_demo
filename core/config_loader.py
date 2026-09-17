# core/config_loader.py  # 配置加载器文件：通常属于自动化测试框架的公共基础层。
# 把 config/env.yaml 配置文件读进来，转成一个全局对象 config，以后测试代码里直接用 config.xxx 就能拿配置。
"""  # 模块说明开始。
配置加载器：单例模式，全局唯一入口  # 统一读取并提供测试环境配置。
"""  # 模块说明结束。
import yaml  # 导入 YAML 解析库，用于读取 env.yaml。
from pathlib import Path  # 导入跨平台路径处理工具。
from types import SimpleNamespace  # 导入可通过属性访问数据的简单对象。


def _dict_to_namespace(d: dict) -> SimpleNamespace:  # 定义内部函数，将配置字典转换为对象。
    """递归把 dict 转成 SimpleNamespace，支持 obj.key 访问"""  # 说明转换支持嵌套字典。
    if not isinstance(d, dict):  # 如果当前值不是字典，说明已经是配置叶子值。
        return d  # 直接返回字符串、数字、列表等原始值。
    ns = SimpleNamespace()  # 创建一个可以动态添加属性的对象。
    for k, v in d.items():  # 遍历当前字典中的每个配置项。
        safe_key = k.replace("-", "_")  # 将连字符替换为下划线，便于使用 obj.key 访问。
        setattr(ns, safe_key, _dict_to_namespace(v))  # 递归转换子值并保存为对象属性。
    return ns  # 返回转换后的配置对象。


class Config:  # 定义配置管理类，封装配置文件读取和访问逻辑。
    _instance = None  # 保存唯一实例，避免重复创建配置对象。
    _data: SimpleNamespace = None  # 保存解析后的配置数据。

    def __new__(cls):  # 重写对象创建方法，实现单例模式。
        if cls._instance is None:  # 仅在第一次使用时执行初始化。
            cls._instance = super().__new__(cls)  # 创建并缓存唯一的 Config 实例。
            config_path = Path(__file__).parent.parent / "config" / "env.yaml"  # 计算配置文件路径。
            with open(config_path, encoding="utf-8") as f:  # 使用 UTF-8 打开配置文件。
                raw = yaml.safe_load(f)  # 安全解析 YAML 内容为 Python 数据。
            cls._data = _dict_to_namespace(raw)  # 将字典转换为可用点号访问的对象。
        return cls._instance  # 后续调用直接返回同一个实例。

    def __getattr__(self, key):  # 当 Config 没有该属性时，转向配置数据中查找。
        return getattr(self._data, key, None)  # 找到则返回配置值，否则返回 None。


config = Config()  # 创建全局配置入口，其他测试模块可直接导入使用。

# 框架组织说明：本模块属于自动化测试框架的配置基础层。
# 测试用例、页面对象和接口封装只需要使用 config，不必关心文件路径和 YAML 解析细节。
# 单例模式保证整个测试运行期间共享同一份配置，避免重复读取和数据不一致。
# 通过集中管理环境地址、账号等参数，可以在切换测试环境时只修改配置文件。