import logging
import logging.config
import os


def setup_logging():
    # Crear el directorio de logs si no existe
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s - %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": "INFO",
            },
            "file_info": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/info.log",
                "maxBytes": 1048576,  # 1 MB
                "backupCount": 5,
                "formatter": "standard",
                "level": "INFO",
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/error.log",
                "maxBytes": 1048576,  # 1 MB
                "backupCount": 5,
                "formatter": "standard",
                "level": "ERROR",
            },
        },
        "loggers": {
            "": {  # Logger raíz
                "handlers": ["console", "file_info", "file_error"],
                "level": "INFO",
                "propagate": True,
            },
            "fetchers": {
                "handlers": ["console", "file_info", "file_error"],
                "level": "INFO",
                "propagate": False,
            },
            "utils": {
                "handlers": ["console", "file_info", "file_error"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
