import json
import logging
import traceback
from datetime import date, datetime, time
from inspect import istraceback
from typing import Dict, Optional, IO, Union, Any
from dataclasses import is_dataclass, asdict


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
    def __init__(self, json_encoder: json.JSONEncoder = JsonEncoder(), **kwargs):
        self.json_encoder = json_encoder
        super(JsonFormatter, self).__init__(**kwargs)

    def format_message(self, record: logging.LogRecord) -> Any:
        if isinstance(record.msg, str):
            return record.msg.format(**getattr(record, "_log_attributes", {}))

        if record.levelname != "DEBUG":
            record.levelname = "ERROR"
            return f"Dumping objects is prohibited at `{record.levelname}` log level."

        return record.msg

    def format_time(self, record: logging.LogRecord) -> str:
        return datetime.utcfromtimestamp(record.created).isoformat()

    def format_extra(self, record: logging.LogRecord) -> Dict[str, str]:
        if hasattr(record, "tags"):
            return {**getattr(record, "tags"), "path": f"{record.module}.{record.funcName}:{record.lineno}"}

        return {"path": f"{record.module}.{record.funcName}:{record.lineno}"}

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "message": self.format_message(record),
            "extra": self.format_extra(record),
            "level": record.levelname,
            "time": self.format_time(record),
        }

        return json.dumps(log, cls=JsonEncoder, ensure_ascii=True)


class Logger(logging.Logger):
    tags: Dict[str, str] = {}

    @classmethod
    def set_tag(cls, key: str, value: str) -> None:
        cls.tags[key] = value

    def handle(self, record: logging.LogRecord) -> None:
        setattr(record, "tags", self.tags)
        super(Logger, self).handle(record)

    def _log(self, *args, **kwargs) -> None:
        if "extra" in kwargs:
            kwargs["extra"] = {"_log_attributes": kwargs["extra"]}
        super(Logger, self)._log(*args, **kwargs)

    @classmethod
    def get(cls, name: str, level: Union[str, int, None] = None, log_stream: Optional[IO[str]] = None) -> "Logger":
        logger = logging.getLogger(name)

        log_handler = logging.StreamHandler(log_stream)
        log_handler.setFormatter(JsonFormatter())

        logger.addHandler(log_handler)
        logger.setLevel(level or logging.DEBUG)

        return logger  # type: ignore


# initialise logging manager with package's class
logging.setLoggerClass(Logger)
