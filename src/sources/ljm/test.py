import unittest
from unittest.mock import MagicMock

import main


# Basic test class
class TestLabJackMock(unittest.TestCase):
    def setUp(self):
        """Create mock before each test"""
        self.mock_ljm = MagicMock()

    def test_basic_stream_start(self):
        """Test that stream starts correctly"""
        # Arrange: set up mock return values.
        self.mock_ljm.openS.return_value = 1

        # Act: call the function to test.
        handle = 1  # Things to test later.

        # Assert: verify the calls and result values.
        self.assertEqual(handle, 1)
        self.mock_ljm.openS.assert_called_once()
        self.mock_ljm.setStreamCallback.assert_called_once()
        self.mock_ljm.eStreamStart.assert_called_once()

    def test_callback_reads_data(self):
        """Test that callback reads stream data"""
        # Arrange: mock the data return values.
        self.mock_ljm.eStreamRead.return_value = {
            "aData": [1.1, 2.2, 3.3],
            "deviceScanBacklog": 0,
            "ljmScanBacklog": 0,
        }

        # Act: call the function to test.
        result = 3  # Things to test later.

        # Assert: verify the calls and result values.
        self.assertEqual(result, 3)
        self.mock_ljm.eStreamRead.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
