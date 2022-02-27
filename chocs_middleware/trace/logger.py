import json
import logging
import traceback
from datetime import date, datetime, time
from inspect import istraceback
from typing import Dict, Optional, IO, Union, Any


class JsonEncoder(json.JSONEncoder):
    def default(self, data: Any) -> Optional[str]:
        if isinstance(data, (date, datetime, time)):
            return data.isoformat()
        elif istraceback(data):
            return "".join(traceback.format_tb(data)).strip()
        elif isinstance(data, Exception):
            return str(data)

        try:
            return str(data)
        except Exception:
            return super(JsonEncoder, self).default(data)


class JsonFormatter(logging.Formatter):

    def __init__(self, json_encoder: json.JSONEncoder = JsonEncoder(), **kwargs):
        self.json_encoder = json_encoder
        super(JsonFormatter, self).__init__(**kwargs)

    def formatMessage(self, record: logging.LogRecord) -> str:
        return record.msg

    def formatTime(self, record: logging.LogRecord, date_format: str = "") -> str:
        return datetime.utcfromtimestamp(record.created).isoformat()

    def formatExtra(self, record: logging.LogRecord) -> Dict[str, str]:
        if hasattr(record, "tags"):
            return {
                **record.tags,
                "path": f"{record.module}.{record.funcName}:{record.lineno}"
            }

        return {
            "path": f"{record.module}.{record.funcName}:{record.lineno}"
        }

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "extra": self.formatExtra(record),
            "message": self.formatMessage(record),
            "level": record.levelname,
            "time": self.formatTime(record),
        }

        return json.dumps(log, cls=JsonEncoder, ensure_ascii=True)


class Logger(logging.Logger):
    tags: Dict[str, str] = {}

    @classmethod
    def add_tag(cls, key: str, value: str) -> None:
        cls.tags[key] = value
        
    def handle(self, record: logging.LogRecord) -> None:
        setattr(record, "tags", self.tags)
        super(Logger, self).handle(record)

    @classmethod
    def get(cls, name: str, level: Union[str, int, None] = None, write_stream: Optional[IO[str]] = None) -> 'Logger':
        logger = logging.getLogger(name)

        log_handler = logging.StreamHandler(write_stream)
        log_handler.setFormatter(JsonFormatter())

        logger.addHandler(log_handler)
        logger.setLevel(level or logging.DEBUG)

        return logger


# initialise logging manager with package's class
logging.setLoggerClass(Logger)
