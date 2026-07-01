from tools.data_processing_v2_beta.main import resolve_daq_channel


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
