"""
Implements the configuration pydantic model
"""
import pydantic


# pylint: disable=too-few-public-methods
class Settings(pydantic.BaseSettings):
    """
    Class for settings, which can be set via environment variables
    """
    class Config(pydantic.BaseConfig):
        """Config class for pydantic"""
        env_file = 'configs/config.dev'
        secrets_dir = 'secrets'

    consumer_key: str
    consumer_secret: str
    token_production: str
    token_sandbox: str
    callback_url: str = 'http://localhost:5555'

    sandbox: bool = True
    directory: str = "D:\\Benutzer\\mstuebner\\Eigene Dateien\\ScanSnap\\Ev-Autoimport"
