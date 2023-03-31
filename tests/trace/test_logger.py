import json
from io import StringIO

from chocs_middleware.trace import Logger
from chocs_middleware.trace.logger import _LogArgsBucket


def test_can_use_format_attribute() -> None:
    # given
    items = {
        "tags": {
            "tag_a": "a",
            "tag_b": "b",
            "multi_tag": {
                "tag_a_a": "a_a",
                "tag_b_b": "b_b",
            }
        },
        "value_a": "1",
        "value_b": "2"
    }

    attrs = _LogArgsBucket(items)

    # when
    assert "{tags.tag_a}".format_map(attrs) == "a"
    assert "{value_a}".format_map(attrs) == "1"


def test_can_instantiate_new_logger() -> None:
    # when
    logger = Logger.get("test_instantiate_log")

    # then
    assert isinstance(logger, Logger)
    assert logger.name == "test_instantiate_log"


def test_can_log_message() -> None:
    # given
    logger_stream = StringIO()
    logger = Logger.get("test_log", log_stream=logger_stream)

    # when
    logger.info("test log")

    # then
    raw_logs = logger_stream.getvalue().split("\n")[:-1]

    for record in raw_logs:
        log = json.loads(record)

        assert "message" in log
        assert "args" in log
        assert "level" in log
        assert "timestamp" in log
        assert "tags" in log


def test_can_interpolate_message() -> None:
    # given
    logger_stream = StringIO()
    logger = Logger.get("test_interpolate_message", log_stream=logger_stream)

    # when
    logger.info("hello {name}", name="test")
    logger.info("start transaction")
    logger.info("end transaction")

    # then
    raw_logs = logger_stream.getvalue().split("\n")[:-1]
    record = raw_logs[0]
    log = json.loads(record)

    assert log["message"] == "hello {name}"
    assert log["args"] == {"name": "test"}
    assert log["level"] == "INFO"
    assert "timestamp" in log
    assert "tags" in log
    assert "source_path" in log["tags"]


def test_can_attach_tags() -> None:
    # given
    logger_stream = StringIO()
    logger = Logger.get(
        "test_can_attach_tags",
        log_stream=logger_stream,
        message_format="[{level}] {tags.x-request-id} - {msg}")

    # when
    Logger.set_tag("x-request-id", "req-1")
    Logger.set_tag("x-causation-id", "caus-2")
    Logger.set_tag("x-correlation-id", "correl-3")

    logger.info("{hello} with tags", hello="hello 1")
    logger.info("{hello} with tags", hello="hello 2")
    logger.info("{hello} with tags", hello="hello 3")

    # then
    raw_logs = logger_stream.getvalue().split("\n")[:-1]

    for record in raw_logs:
        log = json.loads(record)

        assert "tags" in log
        assert "x-request-id" in log
        assert "x-causation-id" in log
        assert "x-correlation-id" in log

        assert log["x-request-id"] == "req-1"
        assert log["x-causation-id"] == "caus-2"
        assert log["x-correlation-id"] == "correl-3"


def test_can_log_a_dict() -> None:
    # given
    logger_stream = StringIO()
    logger = Logger.get("test_can_log_a_dict", log_stream=logger_stream)

    # when
    logger.debug({"test": "ok"})

    # then
    raw_logs = logger_stream.getvalue().split("\n")[:-1]
    record = raw_logs[0]
    log = json.loads(record)

    assert log["message"] == {"test": "ok"}

def test_can_log_with_a_prefix() -> None:
    # given
    logger_stream = StringIO()
    logger = Logger.get("test_can_log_with_a_prefix", log_stream=logger_stream, use_prefix=True)

    # when
    item = {"test": "ok"}
    logger.debug("Test log {item}", item=item)

    # then
    raw_logs = logger_stream.getvalue().split("\n")[:-1]
    record = raw_logs[0]
    string_prefix = record[:record.find('\t')]
    json_payload = json.loads(record[record.find('\t'):])

    assert "Test log {'test': 'ok'}" in string_prefix
    assert json_payload["message"] == 'Test log {item}'

def test_log_a_dict_in_non_debug_level_as_string() -> None:
    # given
    logger_stream = StringIO()
    logger = Logger.get("test_cannot_log_a_dict", log_stream=logger_stream)

    # when
    logger.info({"test": "ok"})

    # then
    raw_logs = logger_stream.getvalue().split("\n")[:-1]
    record = raw_logs[0]
    log = json.loads(record)

    assert log["level"] == "INFO"
    assert log["message"] == str({"test": "ok"})


def test_can_retrieve_same_logger_multiple_times() -> None:
    # given
    logger_stream = StringIO()
    loggers = [
        Logger.get("test_same_logger", log_stream=logger_stream),
        Logger.get("test_same_logger", log_stream=logger_stream),
        Logger.get("test_same_logger", log_stream=logger_stream),
        Logger.get("test_same_logger", log_stream=logger_stream),
        Logger.get("test_same_logger", log_stream=logger_stream),
    ]

    # when
    for logger in loggers:
        logger.info("test")

    # then
    raw_logs = logger_stream.getvalue().split("\n")[:-1]
    assert len(raw_logs) == 5
    for logger in loggers:
        assert isinstance(logger, Logger)
        assert logger == loggers[0]

