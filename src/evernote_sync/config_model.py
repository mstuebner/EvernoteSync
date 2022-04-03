"""
Implements the configuration pydantic model
"""
import pydantic


class Settings(pydantic.BaseSettings):
    """
    Class for settings, which can be set via environment variables
    """
    consumer_key: str
    consumer_secret: str
    callback_url: str = 'http://localhost:5555'
    sandbox: bool = True


settings = Settings()
