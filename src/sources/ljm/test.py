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

class TestLabJackReadData(unittest.TestCase):
    def setUp(self):
        self.mock_ljm = MagicMock()
        main.ljm = self.mock_ljm

        self.mock_sender = MagicMock()
        main.sender = self.mock_sender

        main.calibration.Sensor.parse = MagicMock(return_value={'foo': [9, 8, 7]})
        main.time.time_ns = MagicMock(return_value=1_000_000_000)
        main.time.time = MagicMock(return_value=1.0)

    def test_read_data_processes_interleaved_sensor_values(self):
        self.mock_ljm.eStreamRead.side_effect = [
            ([1, 2, 3, 4, 5, 6], 0, 0),
            KeyboardInterrupt(),
        ]

        with self.assertRaises(KeyboardInterrupt):
            main.read_data(
                handle=1,
                num_addresses=2,
                scans_per_read=3,
                scan_rate=1000,
                quiet=True,
                no_built_in_log=True,
            )

        expected = [[1, 3, 5], [2, 4, 6]]
        main.calibration.Sensor.parse.assert_called_once_with(expected)

        self.mock_sender.send.assert_called_once()
        channel, payload = self.mock_sender.send.call_args[0]
        self.assertEqual(channel, main.CHANNEL)
        self.assertEqual(payload['data'], {'foo': [9, 8, 7]})
        self.assertEqual(payload['message_format_version'], main.MESSAGE_FORMAT_VERSION)
        self.assertEqual(payload['sample_rate'], 1000)
        self.assertEqual(payload['relative_timestamps_nanoseconds'], [1_000_000_000, 1_001_000_000, 1_002_000_000])


if __name__ == '__main__':
    unittest.main()
