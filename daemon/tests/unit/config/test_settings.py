"""Every ``config.toml`` default, plus rejection of bad input (SRD 8.2)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deckhand.config.settings import (
    ActionsSettings,
    LoggingSettings,
    MdnsSettings,
    NotifierSettings,
    RunsSettings,
    SecuritySettings,
    ServerSettings,
    Settings,
    TelemetrySettings,
)


def test_server_defaults() -> None:
    server = Settings().server

    assert server.bind == "0.0.0.0"  # noqa: S104 - asserting the documented default
    assert server.port == 47800
    assert server.allowed_networks == [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "100.64.0.0/10",
        "fe80::/10",
        "fc00::/7",
    ]
    assert server.max_connections == 8
    assert server.max_unauthenticated == 4


def test_allowed_networks_default_is_not_shared() -> None:
    first = Settings().server.allowed_networks
    first.append("203.0.113.0/24")

    assert "203.0.113.0/24" not in Settings().server.allowed_networks


def test_security_defaults() -> None:
    security = Settings().security

    assert security.allow_shell is False
    assert security.remote_layout_edit is True
    assert security.remote_alert_edit is True


def test_runs_defaults() -> None:
    runs = Settings().runs

    assert runs.max_concurrent == 16
    assert runs.default_timeout_sec == 0
    assert runs.kill_grace_sec == 5
    assert runs.kill_on_exit is True
    assert runs.log_buffer_lines == 5000
    assert runs.retain_finished == 20
    assert runs.retain_minutes == 30


def test_telemetry_defaults() -> None:
    telemetry = Settings().telemetry

    assert telemetry.default_interval_ms == 1000
    assert telemetry.libre_hardware_monitor_url == ""


def test_mdns_actions_logging_and_notifier_defaults() -> None:
    settings = Settings()

    assert settings.mdns.enabled is True
    assert settings.actions.watch is True
    assert settings.logging.level == "INFO"
    assert settings.logging.json_file is True
    assert settings.notifier.type == "none"
    assert settings.notifier.url == ""


def test_each_section_is_the_expected_model() -> None:
    settings = Settings()

    assert isinstance(settings.server, ServerSettings)
    assert isinstance(settings.security, SecuritySettings)
    assert isinstance(settings.runs, RunsSettings)
    assert isinstance(settings.telemetry, TelemetrySettings)
    assert isinstance(settings.mdns, MdnsSettings)
    assert isinstance(settings.actions, ActionsSettings)
    assert isinstance(settings.logging, LoggingSettings)
    assert isinstance(settings.notifier, NotifierSettings)


def test_empty_document_is_all_defaults() -> None:
    assert Settings.model_validate({}) == Settings()


def test_unknown_section_is_rejected() -> None:
    with pytest.raises(ValidationError, match="serverr"):
        Settings.model_validate({"serverr": {"port": 1}})


def test_unknown_key_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Settings.model_validate({"server": {"prot": 47800}})

    locations = [error["loc"] for error in excinfo.value.errors()]
    assert ("server", "prot") in locations


@pytest.mark.parametrize(
    "document",
    [
        {"server": {"port": "not-a-number"}},
        {"server": {"port": True}},
        {"runs": {"kill_on_exit": "yes"}},
        {"logging": {"json_file": 1}},
    ],
)
def test_wrong_type_is_rejected(document: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(document)


@pytest.mark.parametrize("port", [0, 65536, -1])
def test_port_out_of_range_is_rejected(port: int) -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"server": {"port": port}})


@pytest.mark.parametrize(
    "document",
    [
        {"server": {"max_connections": 0}},
        {"runs": {"max_concurrent": 0}},
        {"runs": {"log_buffer_lines": 0}},
        {"runs": {"kill_grace_sec": -1}},
        {"telemetry": {"default_interval_ms": 0}},
    ],
)
def test_impossible_counts_are_rejected(document: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(document)


def test_log_level_is_normalized() -> None:
    assert Settings.model_validate({"logging": {"level": " debug "}}).logging.level == "DEBUG"


def test_unknown_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError, match="level must be one of"):
        Settings.model_validate({"logging": {"level": "TRACE"}})


def test_unknown_notifier_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"notifier": {"type": "slack"}})


def test_settings_are_immutable() -> None:
    settings = Settings()

    with pytest.raises(ValidationError):
        settings.server.port = 1
