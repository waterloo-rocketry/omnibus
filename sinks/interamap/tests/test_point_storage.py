import time

import pytest
from PySide6 import QtCore
from PySide6.QtCore import QThread, Signal

from src.data_struct import Point_GPS
from src.point_storage import Point_Storage
from src.real_time_parser import BoardID, RTParser


@pytest.mark.skip(reason="To be implemented properly")
class TestPointStorage():
    mock_gps_RT_data = None  # should be a signal but need to figure out how to mock it
    mock_gps_point = Point_GPS(
        lon=1.0,
        lat=2.0,
        alt=3.0,
        num_sats=4,
        time_stamp=time.time(),
        board_id="GPS"
    )

    received_point = None

    @pytest.fixture(autouse=True)
    def reset_point(self):
        self.received_point = None

    def receive_point(self, point):
        self.received_point = point

    def test_storage_add(self):
        point_storage = Point_Storage(self.mock_gps_RT_data)
        point_storage.storage_update.connect(self.receive_point)
        point_storage.store_point(self.mock_gps_point)

        assert (point_storage.StorageUpdateType.ADD, self.mock_gps_point) == self.received_point
        assert [self.mock_gps_point] == point_storage.get_gps_points()

    def test_storage_remove(self):
        point_storage = Point_Storage(self.mock_gps_RT_data)
        self.mock_gps_RT_data.emit(self.mock_gps_point)

        point_storage.storage_update.connect(self.receive_point)

        point_storage.remove_point(self.mock_gps_point)

        assert (point_storage.StorageUpdateType.REMOVE, self.mock_gps_point) == self.received_point
        assert [] == point_storage.get_gps_points()

    def test_storage_clear(self):
        point_storage = Point_Storage(self.mock_gps_RT_data)
        self.mock_gps_RT_data.emit(self.mock_gps_point)

        point_storage.storage_update.connect(self.receive_point)

        point_storage.clear_points()

        assert (point_storage.StorageUpdateType.CLEAR, None) == self.received_point
        assert [] == point_storage.get_gps_points()
