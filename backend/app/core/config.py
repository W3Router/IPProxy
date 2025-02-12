from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional, ClassVar
import logging.config
import os
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 创建日志目录
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "IP Proxy Management System"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # IPIPV API 配置
    IPPROXY_API_URL: str = "https://sandbox.ipipv.com"
    IPPROXY_APP_KEY: str = "AK20241120145620"
    IPPROXY_APP_SECRET: str = "bf3ffghlt0hpc4omnvc2583jt0fag6a4"
    
    # 日志配置
    LOGGING_CONFIG: ClassVar[Dict[str, Any]] = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': 'INFO'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(LOG_DIR / 'app.log'),  # 使用绝对路径
                'formatter': 'standard',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'level': 'INFO'
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file'],
                'level': 'INFO',
            },
            'app.services.ipipv_base_api': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'app.services.static_order_service': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        }
    }

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# 配置日志
logging.config.dictConfig(settings.LOGGING_CONFIG) 