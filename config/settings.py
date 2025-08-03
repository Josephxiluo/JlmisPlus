"""
配置管理模块
"""
import json
import os


class Settings:
    """配置管理类"""

    def __init__(self):
        self.default_settings = {
            'send_interval': 1000,
            'card_switch': 60,
            'success_threshold': 1000,
            'monitor_numbers': ''
        }
        self.settings = self.default_settings.copy()
        self.config_file = 'sms_pool_config.json'

    def get(self, key, default=None):
        """获取配置项"""
        return self.settings.get(key, default)

    def set(self, key, value):
        """设置配置项"""
        self.settings[key] = value

    def update(self, new_settings):
        """批量更新配置"""
        self.settings.update(new_settings)

    def save_config(self, ports=None, tasks=None):
        """保存配置到文件"""
        config = {
            'settings': self.settings,
        }

        if ports is not None:
            config['ports'] = ports
        if tasks is not None:
            config['tasks'] = tasks

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def load_config(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.settings.update(config.get('settings', {}))
                    return config
        except Exception as e:
            print(f"加载配置失败: {e}")
        return {}

    def reset_to_default(self):
        """重置为默认配置"""
        self.settings = self.default_settings.copy()


# 全局配置实例
settings = Settings()