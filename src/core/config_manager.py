import yaml
import os

class ConfigManager:
    """
    单例配置管理器，处理 YAML 加载与参数合并
    """
    _instance = None

    def __new__(cls, config_path="config/default_config.yaml"):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found at {path}")
        with open(path, 'r', encoding='utf-8') as f:
            self._cfg = yaml.safe_load(f)

    def get(self, key_path, default=None):
        """
        通过 'physics.dt' 这种路径获取配置
        """
        keys = key_path.split('.')
        val = self._cfg
        try:
            for k in keys:
                val = val[k]
            return val
        except (KeyError, TypeError):
            return default

    @property
    def physics(self): return self._cfg['physics']

    @property
    def id_cfg(self): return self._cfg['identification']

    @property
    def viz_cfg(self): return self._cfg['visualization']

    @property
    def exp_cfg(self): return self._cfg['experiment']
