import json
from io import StringIO

from chocs_middleware.trace import Logger


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
    logger.info("test log_message")

    # then
    raw_logs = logger_stream.getvalue().split("\n")
    logs = [json.loads(record) for record in raw_logs if record]

    assert len(logs) == 1
    assert "level" in logs[0]
    assert "time" in logs[0]
    assert "extra" in logs[0]
    assert "message" in logs[0]


def test_can_interpolate_message() -> None:
    # given
    logger_stream = StringIO()
    logger = Logger.get("test_interpolate_message", log_stream=logger_stream)

    # when
    logger.info("hello {name}", extra={"name": "test"})

    # then
    raw_logs = logger_stream.getvalue().split("\n")
    logs = [json.loads(record) for record in raw_logs if record]

    assert logs[0]["message"] == "hello test"


def test_can_attach_tags() -> None:
    # given
    logger_stream = StringIO()
    logger = Logger.get("test_can_attach_tags", log_stream=logger_stream)

    # when
    Logger.set_tag("x-request-id", "1")
    Logger.set_tag("x-causation-id", "2")
    Logger.set_tag("x-correlation-id", "3")

    logger.info("hello 1 with tags")
    logger.info("hello 2 with tags")
    logger.info("hello 3 with tags")

    # then
    raw_logs = logger_stream.getvalue().split("\n")
    logs = [json.loads(record) for record in raw_logs if record]

    for log in logs:
        assert "extra" in log
        assert "x-request-id" in log["extra"]
        assert "x-causation-id" in log["extra"]
        assert "x-correlation-id" in log["extra"]

        assert log["extra"]["x-request-id"] == "1"
        assert log["extra"]["x-causation-id"] == "2"
        assert log["extra"]["x-correlation-id"] == "3"


def test_can_log_a_dict() -> None:
    # given
    logger_stream = StringIO()
    logger = Logger.get("test_can_log_a_dict", log_stream=logger_stream)

    # when
    logger.debug({"test": "ok"})

    # then
    raw_logs = logger_stream.getvalue().split("\n")
    logs = [json.loads(record) for record in raw_logs if record]

    assert logs[0]["message"] == {"test": "ok"}


def test_fail_log_a_dict_in_non_debug_level() -> None:
    # given
    logger_stream = StringIO()
    logger = Logger.get("test_can_log_a_dict", log_stream=logger_stream)

    # when
    logger.info({"test": "ok"})

    # then
    raw_logs = logger_stream.getvalue().split("\n")
    logs = [json.loads(record) for record in raw_logs if record]

    assert logs[0]["level"] == "ERROR"
