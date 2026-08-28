import logging
import sys

from loguru import logger

# from app.core.config import get_settings

# settings = get_settings()


class InterceptHandler(logging.Handler):
    """Перенаправляет стандартный logging в Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2

        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(
            depth=depth,
            exception=record.exc_info,
        ).log(level, record.getMessage())


def configure_logger(log_level: str = "INFO") -> None:
    """Настраивает логирование приложения."""

    logger.remove()

    logger.configure(
        extra={
            "request_id": "-",
        }
    )

    # Консоль
    logger.add(
        sys.stderr,
        level=log_level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[request_id]}</cyan> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    # Общий лог
    logger.add(
        "logs/app.log",
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{extra[request_id]} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )

    # Ошибки
    logger.add(
        "logs/errors.log",
        level="ERROR",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{extra[request_id]} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        rotation="5 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        encoding="utf-8",
    )

    logging.basicConfig(
        handlers=[InterceptHandler()],
        level=0,
        force=True,
    )

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "fastapi",
        # "gunicorn",
        # "gunicorn.error",
    ):
        std_logger = logging.getLogger(logger_name)
        std_logger.handlers = [InterceptHandler()]
        std_logger.propagate = False


# configure_logger(settings.logs_level)