"""Public configuration in SQLite; credentials in OS keyring or environment."""
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit

SECRET_ENV = {'llm_api_key': 'STUDIO_LLM_API_KEY', 'ark_api_key': 'ARK_API_KEY',
              'wavespeed_api_key': 'WAVESPEED_API_KEY',
              'flova_api_key': 'FLOVA_API_KEY', 'pinterest_access_token': 'PINTEREST_ACCESS_TOKEN'}
PUBLIC_ENV = {'llm_base_url': 'STUDIO_LLM_BASE_URL', 'llm_model': 'STUDIO_LLM_MODEL',
              'video_provider': 'STUDIO_VIDEO_PROVIDER', 'ark_model': 'ARK_SEEDANCE_MODEL',
              'wavespeed_model': 'WAVESPEED_VIDEO_MODEL', 'wavespeed_resolution': 'WAVESPEED_VIDEO_RESOLUTION',
              'flova_model': 'FLOVA_VIDEO_MODEL', 'flova_resolution': 'FLOVA_VIDEO_RESOLUTION',
              'flova_cli_path': 'FLOVA_CLI_PATH', 'pinterest_board_id': 'PINTEREST_BOARD_ID'}
PUBLIC_DEFAULTS = {'llm_base_url': 'https://api.deepseek.com',
                   'llm_model': 'deepseek-v4-flash-vision-exp',
                   'video_provider': 'wavespeed', 'ark_model': 'doubao-seedance-2-0-mini-260615',
                   'wavespeed_model': 'bytedance/seedance-2.0-mini/text-to-video', 'wavespeed_resolution': '480p',
                   'flova_model': 'Seedance 2.5', 'flova_resolution': '720p', 'flova_cli_path': 'flova'}
SERVICE = 'videoX-brazil-ugc-studio'


class ConfigurationError(ValueError):
    pass


class Settings:
    def __init__(self, store):
        self.store = store

    def secret(self, name):
        if os.getenv(SECRET_ENV[name]):
            return os.environ[SECRET_ENV[name]].strip()
        if sys.platform != 'win32':
            return ''
        try:
            import keyring
            return keyring.get_password(SERVICE, name) or ''
        except Exception:
            return ''

    def get(self):
        saved = self.store.public_settings()
        return {key: saved.get(key, os.getenv(env, PUBLIC_DEFAULTS.get(key, ''))) for key, env in PUBLIC_ENV.items()}

    def require(self, provider):
        config = self.get()
        if provider == 'llm' and (not config['llm_base_url'] or not config['llm_model'] or not self.secret('llm_api_key')):
            raise ConfigurationError('请在设置中配置 DeepSeek 视觉导演 API Key；默认模型为 deepseek-v4-flash-vision-exp。')
        if provider == 'ark' and not self.secret('ark_api_key'):
            raise ConfigurationError('请在设置中配置火山方舟 ARK API Key，并确认 Seedance 2.0 权限。')
        if provider == 'wavespeed' and not self.secret('wavespeed_api_key'):
            raise ConfigurationError('请在设置中配置 WaveSpeed API Key。人物、场景和游戏图会上传到 WaveSpeed 作为生成参考。')
        if provider == 'flova':
            cli = config['flova_cli_path']
            available = Path(cli).expanduser().is_file() or bool(shutil.which(cli))
            if not available:
                for candidate in [Path.home() / '.local/bin/flova', Path.home() / '.local/bin/flova.exe']:
                    if candidate.is_file():
                        available = True
                        break
            credential = self.secret('flova_api_key') or (Path.home() / '.flova/credentials.yaml').is_file()
            if not available:
                raise ConfigurationError('未找到 Flova CLI。请先按官方接入指引安装，或在设置中填写 CLI 路径。')
            if not credential:
                raise ConfigurationError('请在设置中填入你自己的 Flova Agent API Key。')
        if provider == 'pinterest' and (not self.secret('pinterest_access_token') or not config['pinterest_board_id']):
            raise ConfigurationError('请在设置中配置 Pinterest Access Token 和已授权 Board ID。')

    def public(self):
        result = self.get()
        configured = {}
        for provider in ['llm', 'wavespeed', 'flova', 'ark', 'pinterest']:
            try:
                self.require(provider)
                configured[provider] = True
            except ConfigurationError:
                configured[provider] = False
        result.update(configured=configured, credential_storage='Windows 凭据管理器；环境变量优先' if sys.platform == 'win32' else '密钥仅从环境变量读取')
        return result

    def update(self, data):
        if data.get('llm_base_url'):
            url = urlsplit(data['llm_base_url'])
            if url.username or url.password or url.query or url.fragment or (url.scheme != 'https' and not (url.scheme == 'http' and url.hostname in ['localhost', '127.0.0.1'])):
                raise ConfigurationError('模型地址需为 HTTPS，或本地 http://127.0.0.1 地址，不允许内嵌密钥。')
        if data.get('pinterest_board_id') and not data['pinterest_board_id'].isdigit():
            raise ConfigurationError('Pinterest Board ID 应为数字。')
        # Blank key means preserve the existing credential, never overwrite it accidentally.
        for key in SECRET_ENV:
            if data.get(key):
                try:
                    if sys.platform != 'win32':
                        raise RuntimeError('Use environment variables on non-Windows hosts')
                    import keyring
                    backend = keyring.get_keyring()
                    if backend.priority <= 0 or 'plaintext' in type(backend).__name__.lower():
                        raise RuntimeError('No secure keyring')
                    keyring.set_password(SERVICE, key, data[key])
                except Exception as exc:
                    raise ConfigurationError(f'系统安全凭据存储不可用；请使用环境变量 {SECRET_ENV[key]}，密钥未写入普通文件。') from exc
        self.store.save_settings({k: v for k, v in data.items() if k in PUBLIC_ENV and v is not None})
        return self.public()
