import sys
from pathlib import Path

import pytest

from tools.data_processing_v2_beta import main as main_module
from tools.data_processing_v2_beta.main import resolve_daq_channel, run_daq_command


def test_resolve_daq_channel_defaults_to_auto_detect():
    assert resolve_daq_channel(None) is None


def test_resolve_daq_channel_maps_known_sources():
    assert resolve_daq_channel("ni") == "DAQ/ni"
    assert resolve_daq_channel("ljm") == "DAQ/ljm"
    assert resolve_daq_channel("fake") == "DAQ/Fake"


def test_resolve_daq_channel_preserves_explicit_channel_name():
    assert resolve_daq_channel("DAQ/ni") == "DAQ/ni"
    assert resolve_daq_channel("DAQ") == "DAQ"


def test_resolve_daq_channel_supports_fake_flag():
    assert resolve_daq_channel("ni", use_fake=True) == "DAQ/Fake"


def test_run_daq_command_rejects_host_sync_without_v3(tmp_path: Path):
    input_file = tmp_path / "input.msgpack"
    input_file.write_bytes(b"")

    with pytest.raises(ValueError, match="incompatible with --v2"):
        run_daq_command(str(input_file), None, "DAQ/ni", v3=False, host_sync=True)


def test_main_routes_host_sync_flag_to_daq_runner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    input_file = tmp_path / "input.msgpack"
    input_file.write_bytes(b"")
    captured: dict[str, object] = {}

    def fake_run_daq_command(
        input_path: str,
        output_file: str | None,
        channel: str | None,
        v3: bool = False,
        host_sync: bool = False,
    ) -> None:
        captured["input_path"] = input_path
        captured["output_file"] = output_file
        captured["channel"] = channel
        captured["v3"] = v3
        captured["host_sync"] = host_sync

    monkeypatch.setattr(main_module, "run_daq_command", fake_run_daq_command)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "data-processing-v2",
            "daq",
            str(input_file),
            "--source",
            "ni",
            "--host-sync",
        ],
    )

    main_module.main()

    assert captured == {
        "input_path": str(input_file),
        "output_file": None,
        "channel": "DAQ/ni",
        "v3": True,
        "host_sync": True,
    }


def test_main_routes_host_sync_without_source_to_all_sources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    input_file = tmp_path / "input.msgpack"
    input_file.write_bytes(b"")
    captured: dict[str, object] = {}

    def fake_run_daq_command(
        input_path: str,
        output_file: str | None,
        channel: str | None,
        v3: bool = False,
        host_sync: bool = False,
    ) -> None:
        captured["input_path"] = input_path
        captured["channel"] = channel
        captured["v3"] = v3
        captured["host_sync"] = host_sync

    monkeypatch.setattr(main_module, "run_daq_command", fake_run_daq_command)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "data-processing-v2",
            "daq",
            str(input_file),
            "--host-sync",
        ],
    )

    main_module.main()

    assert captured == {
        "input_path": str(input_file),
        "channel": None,
        "v3": True,
        "host_sync": True,
    }


def test_main_uses_v2_parser_when_requested(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    input_file = tmp_path / "input.msgpack"
    input_file.write_bytes(b"")
    captured: dict[str, object] = {}

    def fake_run_daq_command(
        input_path: str,
        output_file: str | None,
        channel: str | None,
        v3: bool = True,
        host_sync: bool = False,
    ) -> None:
        captured["input_path"] = input_path
        captured["channel"] = channel
        captured["v3"] = v3
        captured["host_sync"] = host_sync

    monkeypatch.setattr(main_module, "run_daq_command", fake_run_daq_command)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "data-processing-v2",
            "daq",
            str(input_file),
            "--source",
            "ni",
            "--v2",
        ],
    )

    main_module.main()

    assert captured == {
        "input_path": str(input_file),
        "channel": "DAQ/ni",
        "v3": False,
        "host_sync": False,
    }
