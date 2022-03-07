import json
import logging
import traceback
from dataclasses import is_dataclass, asdict
from datetime import date, datetime, time
from inspect import istraceback
from typing import Dict, Optional, IO, Union, Any

LOG_PROTECTED_KWARGS = ("exc_info", "stack_info", "stacklevel", "extra")
LOG_RECORD_FIELDS = (
    "args",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "msg",
    "pathname",
    "process",
    "processName",
    "stack_info",
    "thread",
    "threadName",
)


class _LogArgsBucket:
    def __init__(self, args: Dict[str, Any]) -> None:
        self._args = args

    def __getitem__(self, item: str) -> Any:
        return self.__getattr__(item)

    def __getattr__(self, item: str) -> Any:
        if item in self._args:
            if isinstance(self._args[item], dict):
                return _LogArgsBucket(self._args[item])

            return str(self._args[item])
        else:
            return ""

    def __str__(self) -> str:
        return str(self._args)


class JsonEncoder(json.JSONEncoder):
    def default(self, data: Any) -> Any:
        if isinstance(data, (date, datetime, time)):
            return data.isoformat()
        elif istraceback(data):
            return "".join(traceback.format_tb(data)).strip()
        elif is_dataclass(data):
            return asdict(data)
        elif isinstance(data, Exception):
            return str(data)

        try:
            return str(data)
        except Exception:
            return repr(data)


class JsonFormatter(logging.Formatter):
    def __init__(self, json_encoder: json.JSONEncoder = JsonEncoder(), message_format: str = "[{level}] {time} {msg}"):
        self.json_encoder = json_encoder
        self.message_format = message_format
        super(JsonFormatter, self).__init__()

    @staticmethod
    def get_message(record: logging.LogRecord) -> Any:
        if isinstance(record.msg, str):
            return record.msg

        if record.levelname != "DEBUG":
            msg = f"Dumping objects is prohibited at `{record.levelname}` log level."
            record.levelname = "ERROR"
            return msg

        return record.msg

    @staticmethod
    def format_tags(record: logging.LogRecord) -> Dict[str, str]:
        if hasattr(record, "tags"):
            return {**getattr(record, "tags"), "source_path": f"{record.module}.{record.funcName}:{record.lineno}"}

        return {"path": f"{record.module}.{record.funcName}:{record.lineno}"}

    def format_message(self, log_entry: dict) -> str:
        return self.message_format.format_map(_LogArgsBucket(log_entry))

    def format(self, record: logging.LogRecord) -> str:
        message = self.get_message(record)

        if hasattr(record, "_message_kwargs") and record._message_kwargs:  # type: ignore
            msg = message.format(**record._message_kwargs)  # type: ignore
        else:
            msg = message

        payload = {
            "value": message,
            "args": getattr(record, "_message_kwargs", {}),
            "level": record.levelname,
            "time": datetime.utcfromtimestamp(record.created).isoformat(),
            "tags": self.format_tags(record),
        }

        log = {}
        for key in LOG_RECORD_FIELDS:
            if not hasattr(record, key):
                continue
            log[key] = getattr(record, key)

        log = {**log, **payload, **{"msg": msg}}

        return self.format_message(log) + "\t" + json.dumps(payload, cls=JsonEncoder, ensure_ascii=True)


class Logger(logging.Logger):
    tags: Dict[str, str] = {}

    @classmethod
    def set_tag(cls, key: str, value: str) -> None:
        cls.tags[key] = value

    def handle(self, record: logging.LogRecord) -> None:
        setattr(record, "tags", self.tags)
        super(Logger, self).handle(record)

    def _log(self, *args, **kwargs) -> None:
        new_kwargs: Dict[str, Any] = {"extra": {"_message_kwargs": {}}}
        for key, value in kwargs.items():
            if key in LOG_PROTECTED_KWARGS:
                new_kwargs[key] = value
                if key == "extra":
                    new_kwargs["extra"]["_message_kwargs"] = {}
                continue
            new_kwargs["extra"]["_message_kwargs"][key] = value

        super(Logger, self)._log(*args, **new_kwargs)

    @classmethod
    def get(
        cls,
        name: str,
        level: Union[str, int, None] = None,
        log_stream: Optional[IO[str]] = None,
        message_format: str = "[{level}] {time} {msg}",
        propagate: bool = False,
    ) -> "Logger":
        logger = logging.getLogger(name)

        # if logger already has handlers we should clear them up
        if len(logger.handlers) > 1:
            logger.handlers.clear()

        json_handler = logging.StreamHandler(log_stream)
        json_handler.setFormatter(JsonFormatter(message_format=message_format))
        logger.addHandler(json_handler)

        logger.setLevel(level or logging.DEBUG)
        logger.propagate = propagate

        return logger  # type: ignore


# initialise logging manager with package's class
logging.setLoggerClass(Logger)
