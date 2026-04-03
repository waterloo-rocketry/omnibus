import sys
import time
import types
import pytest
import multiprocessing as mp
from unittest.mock import MagicMock

# Prevent main.py from attempting to load the real LabJack library or a
# non-existent config module during import.  The original tests imported
# `main` at the top level which triggered those side-effects and produced
# a DLL-not-found error and a missing-config failure.
#
# By injecting mocks into sys.modules before importing, we keep the module
# import lightweight and safe.

@pytest.fixture(scope="module", autouse=True)
def process_wide_mocks():
    # Preserve original values for clean teardown
    original_labjack = sys.modules.get("labjack")
    original_labjack_ljm = sys.modules.get("labjack.ljm")
    original_config = sys.modules.get("config")

    # Fake LabJack module used by main
    fake_ljm = MagicMock()
    sys.modules["labjack"] = MagicMock()
    sys.modules["labjack.ljm"] = fake_ljm

    # Fake config module used by main
    fake_config = types.SimpleNamespace(
        RATE=1,
        SCAN_RATE=1,
        SCANS_PER_READ=1,
        READ_BULK=1,
        setup=lambda: None,
    )
    sys.modules["config"] = fake_config

    # Ensure Omnibus server IP does not leak between tests
    from omnibus.omnibus import OmnibusCommunicator
    previous_ip = OmnibusCommunicator.server_ip
    OmnibusCommunicator.server_ip = "127.0.0.1"

    try:
        yield
    finally:
        # restore sys.modules entries
        if original_labjack is None:
            sys.modules.pop("labjack", None)
        else:
            sys.modules["labjack"] = original_labjack

        if original_labjack_ljm is None:
            sys.modules.pop("labjack.ljm", None)
        else:
            sys.modules["labjack.ljm"] = original_labjack_ljm

        if original_config is None:
            sys.modules.pop("config", None)
        else:
            sys.modules["config"] = original_config

        # restore Omnibus IP
        OmnibusCommunicator.server_ip = previous_ip


from omnibus.omnibus import OmnibusCommunicator
from omnibus import Receiver, server

def get_main():
    OmnibusCommunicator.server_ip = "127.0.0.1"
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0]]
    try:
        import main
        return main
    finally:
        sys.argv = original_argv
     
def run_server():
    import sys
    sys.argv = [sys.argv[0]]
    from omnibus import server
    # Mock get_ip to return localhost
    original_get_ip = server.get_ip
    server.get_ip = lambda: "127.0.0.1"
    try:
        server.server()
    finally:
        server.get_ip = original_get_ip

@pytest.fixture(scope="module")
def main_module(process_wide_mocks):
    # Ensure module-scoped process patching is installed before importing main.
    return get_main()

@pytest.fixture(scope="module", autouse=True)
def omnibus_server(main_module):
    # Start the Omnibus server in a separate process
    ctx = mp.get_context("spawn")
    server_process = ctx.Process(target=run_server)
    server_process.start()
    OmnibusCommunicator.server_ip = "127.0.0.1"  # skip discovery
    
    try:
        start = time.time()

        # Wait until the server is alive
        s = main_module.sender
        r = Receiver("_ALIVE")
        while r.recv(1) is None:
            s.send("_ALIVE", "_ALIVE")
            if time.time() - start > 5:
                raise TimeoutError("Server did not start within 5 seconds")
        
        yield
    finally:
        # Stop the server    
        server_process.terminate()
        server_process.join()


@pytest.fixture
def test_setup(main_module):    
    mock_ljm = MagicMock()
    main_module.ljm = mock_ljm
    
    receiver = Receiver(main_module.CHANNEL)
    time.sleep(0.05)  # let the receiver connect

    main_module.calibration.Sensor.parse = MagicMock(return_value={'foo': [9, 8, 7]})
    main_module.time.time_ns = MagicMock(return_value=1_000_000_000)
    main_module.time.time = MagicMock(return_value=1.0)
    
    return main_module, mock_ljm, receiver


def test_read_data_processes_interleaved_sensor_values(test_setup):
    main_module, mock_ljm, receiver = test_setup
    
    mock_ljm.eStreamRead.side_effect = [
        ([1, 2, 3, 4, 5, 6], 0, 0),
        KeyboardInterrupt(),
    ]

    with pytest.raises(KeyboardInterrupt):
        main_module.read_data(
            handle=1,
            num_addresses=2,
            scans_per_read=3,
            scan_rate=1000,
            quiet=True,
            no_built_in_log=True,
        )

    expected = [[1, 3, 5], [2, 4, 6]]
    main_module.calibration.Sensor.parse.assert_called_once_with(expected)

    # Receive the message from the server
    message = receiver.recv_message(timeout=1000)  # 1 second timeout
    assert message is not None
    assert message.channel == main_module.CHANNEL
    assert message.payload['data'] == {'foo': [9, 8, 7]}
    assert message.payload['message_format_version'] == main_module.MESSAGE_FORMAT_VERSION
    assert message.payload['sample_rate'] == 1000
    assert message.payload['relative_timestamps_nanoseconds'] == [
        1_000_000_000,
        1_001_000_000,
        1_002_000_000,
    ]
