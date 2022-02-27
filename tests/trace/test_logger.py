from io import BytesIO

from chocs_middleware.trace import Logger


def test_can_instantiate_new_logger() -> None:
    # when
    logger = Logger.get("test_log")

    # then
    assert isinstance(logger, Logger)
    assert logger.name == "test_log"


def test_can_log_message() -> None:
    # given
    logger_stream = BytesIO()
    logger = Logger.get("test_log", write_stream=logger_stream)

    # when
    logger.info("test message %a%", extra={"something": "extra"})

    # then
    assert False
