from src.logger_config import configure_logger


def test_info_level_hides_debug_messages(monkeypatch, capsys):
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    logger = configure_logger("test_logger_info")

    logger.debug("detailed progress")
    logger.info("important result")

    output = capsys.readouterr().out

    assert "detailed progress" not in output
    assert "important result" in output


def test_debug_level_shows_debug_messages(monkeypatch, capsys):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    logger = configure_logger("test_logger_debug")

    logger.debug("detailed progress")
    logger.info("important result")

    output = capsys.readouterr().out

    assert "detailed progress" in output
    assert "important result" in output
