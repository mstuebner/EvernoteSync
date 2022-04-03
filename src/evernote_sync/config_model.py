"""
Implements the configuration pydantic model
"""
import pydantic


# pylint: disable=too-few-public-methods
class Settings(pydantic.BaseSettings):
    """
    Class for settings, which can be set via environment variables
    """
    consumer_key: str
    consumer_secret: str
    callback_url: str = 'http://localhost:5555'
    sandbox: bool = True


settings = Settings()
