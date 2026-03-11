import sys
import types
import unittest
from unittest.mock import MagicMock, patch, mock_open

# Prevent main.py from attempting to load the real LabJack library or a
# non-existent config module during import.  The original tests imported
# `main` at the top level which triggered those side-effects and produced
# a DLL-not-found error and a missing-config failure.
#
# By injecting mocks into sys.modules before importing, we keep the module
# import lightweight and safe.

# create a fake labjack.ljm module with the pieces used by main
fake_ljm = MagicMock()
# also create the parent package so the import system is happy
sys.modules["labjack"] = MagicMock()
sys.modules["labjack.ljm"] = fake_ljm

# create a dummy config module with the constants and setup() used in main
fake_config = types.SimpleNamespace(
    RATE=1,
    SCAN_RATE=1,
    SCANS_PER_READ=1,
    READ_BULK=1,
    setup=lambda: None,
)
sys.modules["config"] = fake_config

# provide a lightweight msgpack stub used by main
import types as _types
fake_msgpack = _types.ModuleType("msgpack")
fake_msgpack.packb = lambda x: b""
fake_msgpack.unpackb = lambda x: {}
# add exceptions submodule for calibration import
fake_exceptions = _types.SimpleNamespace(PackException=Exception)
fake_msgpack.exceptions = fake_exceptions
sys.modules["msgpack"] = fake_msgpack
sys.modules["msgpack.exceptions"] = fake_exceptions

# stub the omnibus package and its Sender class used by main
fake_omnibus = types.SimpleNamespace(Sender=lambda: MagicMock())
sys.modules["omnibus"] = fake_omnibus

import main


# Tests for the LabJack streaming and data‑processing logic in `ljm/main.py`.
#
# The earlier version of this file merely checked that LJM functions were
# invoked; the goal here is to exercise the conversion/calibration logic that
# occurs inside the callback and to make sure the message sent to Omnibus has a
# valid structure.

# Basic test class
class TestLabJackMock(unittest.TestCase):
    def setUp(self):
        """Create mocks and reset global state before each test."""
        # Patch the ljm module inside main so that no actual device calls are made.
        self.mock_ljm = MagicMock()
        main.ljm = self.mock_ljm

        # Prevent the real sender from trying to send anything over the network.
        self.mock_sender = MagicMock()
        main.sender = self.mock_sender

        # Make sure the global stream_info is in a known clean state for callback tests.
        main.stream_info = main.StreamInfo()

    def test_basic_stream_start(self):
        """Starting the stream should make the expected LJM calls."""
        # Arrange: configure the mock behaviors that main.main() relies on.
        self.mock_ljm.openS.return_value = 5
        self.mock_ljm.getHandleInfo.return_value = (1, 2, 3, 0, 0, 0)
        self.mock_ljm.eStreamStart.return_value = 42

        # Force the callback registration to raise KeyboardInterrupt so main() exits
        # quickly and the test doesn't hang.
        def raise_keyboard_interrupt(handle, callback):
            raise KeyboardInterrupt()

        self.mock_ljm.setStreamCallback.side_effect = raise_keyboard_interrupt

        # Patch file writes so we don't create actual log files.
        with patch("builtins.open", mock_open()):
            main.main()

        self.mock_ljm.openS.assert_called_once_with("T7", "ANY", "ANY")
        self.mock_ljm.eWriteName.assert_any_call(5, "STREAM_TRIGGER_INDEX", 0)
        self.mock_ljm.eWriteName.assert_any_call(5, "STREAM_CLOCK_SOURCE", 0)
        self.mock_ljm.eStreamStart.assert_called_once()
        self.mock_ljm.setStreamCallback.assert_called_once()

    def test_callback_processes_and_sends_data(self):
        """Callback should convert raw `aData` and send a properly formed message."""
        # Prepare stream_info so the callback has everything it expects.
        si = main.stream_info
        si.handle = 1
        si.numAddresses = 2
        si.scansPerRead = 3
        si.relative_last_read_time = 100

        # Provide a predictable calibration result.
        main.calibration.Sensor.parse = MagicMock(return_value={"foo": [9, 8, 7]})

        # Mock the raw stream read.  The interleaved sequence below represents
        # two channels and three scans.
        self.mock_ljm.eStreamRead.return_value = ([1, 2, 3, 4, 5, 6], 0, 0)

        with patch("builtins.open", mock_open()) as fake_open:
            # Act: invoke the callback as LJM would.
            main.ljm_stream_read_callback(si.handle)

        # The nested list conversion should have been performed correctly.
        expected_nested = [[1, 3, 5], [2, 4, 6]]
        main.calibration.Sensor.parse.assert_called_once_with(expected_nested)

        # Sender should have been called once with channel and message dict.
        self.mock_sender.send.assert_called_once()
        sent_channel, msg = self.mock_sender.send.call_args[0]
        self.assertEqual(sent_channel, main.CHANNEL)

        # Basic structural assertions on the message.
        self.assertEqual(msg["data"], {"foo": [9, 8, 7]})
        self.assertEqual(msg["message_format_version"], main.MESSAGE_FORMAT_VERSION)
        self.assertEqual(msg["sample_rate"], int(main.config.RATE))
        self.assertEqual(len(msg["relative_timestamps_nanoseconds"]), 3)

        # The log file should have been opened for append and written to once.
        fake_open.assert_called()



if __name__ == "__main__":
    unittest.main()
