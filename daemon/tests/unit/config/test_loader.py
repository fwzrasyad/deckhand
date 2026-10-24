"""Loading ``config.toml``: defaults, parsing, and clear errors (SRD 8.2)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from deckhand.config.loader import ConfigError, load_config
from deckhand.config.paths import config_file
from deckhand.config.settings import Settings
from deckhand.core.errors import ConfigurationError

SRD_EXAMPLE = textwrap.dedent(
    """
    [server]
    bind = "0.0.0.0"
    port = 47800
    allowed_networks = [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "100.64.0.0/10",
        "fe80::/10",
        "fc00::/7",
    ]
    max_connections = 8
    max_unauthenticated = 4

    [security]
    allow_shell = false
    remote_layout_edit = true
    remote_alert_edit = true

    [runs]
    max_concurrent = 16
    default_timeout_sec = 0
    kill_grace_sec = 5
    kill_on_exit = true
    log_buffer_lines = 5000
    retain_finished = 20
    retain_minutes = 30

    [telemetry]
    default_interval_ms = 1000
    libre_hardware_monitor_url = ""

    [mdns]
    enabled = true

    [actions]
    watch = true

    [logging]
    level = "INFO"
    json_file = true

    [notifier]
    type = "none"
    url = ""
    """
)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_missing_file_means_all_defaults(tmp_path: Path) -> None:
    assert load_config(tmp_path / "absent.toml") == Settings()


def test_default_path_uses_the_config_directory(deckhand_home: Path) -> None:
    assert not config_file().exists()

    assert load_config() == Settings()


def test_default_path_reads_the_override(
    deckhand_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(config_file(), "[server]\nport = 5000\n")
    monkeypatch.setenv("DECKHAND_HOME", str(deckhand_home))

    assert load_config().server.port == 5000


def test_empty_file_means_all_defaults(tmp_path: Path) -> None:
    assert load_config(_write(tmp_path / "config.toml", "")) == Settings()


def test_partial_file_keeps_other_defaults(tmp_path: Path) -> None:
    settings = load_config(_write(tmp_path / "config.toml", "[server]\nport = 5001\n"))

    assert settings.server.port == 5001
    assert settings.server.max_connections == Settings().server.max_connections
    assert settings.runs == Settings().runs


def test_explicit_srd_example_is_accepted(tmp_path: Path) -> None:
    settings = load_config(_write(tmp_path / "config.toml", SRD_EXAMPLE))

    assert settings.server.port == 47800
    assert len(settings.server.allowed_networks) == 7
    assert settings.security.allow_shell is False
    assert settings.runs.retain_minutes == 30
    assert settings.logging.level == "INFO"
    assert settings.notifier.type == "none"


def test_values_from_the_file_win(tmp_path: Path) -> None:
    document = """
        [server]
        bind = "127.0.0.1"
        port = 47999

        [security]
        allow_shell = true

        [notifier]
        type = "ntfy"
        url = "https://ntfy.example/topic"
    """
    settings = load_config(_write(tmp_path / "config.toml", textwrap.dedent(document)))

    assert settings.server.bind == "127.0.0.1"
    assert settings.server.port == 47999
    assert settings.security.allow_shell is True
    assert settings.notifier.url == "https://ntfy.example/topic"


def test_malformed_toml_is_a_clear_error(tmp_path: Path) -> None:
    path = _write(tmp_path / "config.toml", "[server\nport = 1\n")

    with pytest.raises(ConfigError, match="invalid TOML") as excinfo:
        load_config(path)

    assert str(path) in str(excinfo.value)
    assert excinfo.value.path == path


def test_unknown_key_is_a_clear_error(tmp_path: Path) -> None:
    path = _write(tmp_path / "config.toml", "[server]\nprot = 47800\n")

    with pytest.raises(ConfigError, match="invalid configuration") as excinfo:
        load_config(path)

    assert "server.prot" in str(excinfo.value)


def test_wrong_type_is_a_clear_error(tmp_path: Path) -> None:
    path = _write(tmp_path / "config.toml", '[runs]\nmax_concurrent = "many"\n')

    with pytest.raises(ConfigError) as excinfo:
        load_config(path)

    assert "runs.max_concurrent" in str(excinfo.value)
    assert str(path) in str(excinfo.value)


def test_non_utf8_file_is_a_clear_error(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_bytes(b"\xff\xfe[server]\n")

    with pytest.raises(ConfigError, match="not valid utf-8"):
        load_config(path)


def test_unreadable_path_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="cannot read config file"):
        load_config(tmp_path)


def test_config_error_is_a_configuration_error(tmp_path: Path) -> None:
    path = _write(tmp_path / "config.toml", "[server]\nport = 0\n")

    with pytest.raises(ConfigurationError) as excinfo:
        load_config(path)

    assert isinstance(excinfo.value, ConfigError)
    assert excinfo.value.details["path"] == str(path)
