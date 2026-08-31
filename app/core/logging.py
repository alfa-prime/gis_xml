import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    """Перенаправляет стандартный logging в Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # Не дублируем traceback HTTP-ошибок: их уже пишет глобальный handler.
        if record.name.startswith("uvicorn") and record.getMessage().startswith(
            "Exception in ASGI application"
        ):
            return

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

    logger.add(
        sys.stderr,
        level=log_level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[request_id]}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    logger.add(
        "logs/app.log",
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{extra[request_id]} | "
            "{message}"
        ),
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )

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

    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "fastapi",
    ):
        std_logger = logging.getLogger(logger_name)
        std_logger.handlers = [InterceptHandler()]
        std_logger.propagate = False
