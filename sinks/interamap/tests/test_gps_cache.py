import time

import pytest

from src.data_struct import Point_GPS
from src.gps_cache import GPS_Cache


class TestGPSCache():
    mock_gps_point_1 = Point_GPS(
        lon=1.0,
        lat=2.0,
        alt=3.0,
        num_sats=4,
        time_stamp=time.time(),
        board_id="GPS"
    )

    mock_gps_point_2 = Point_GPS(
        lon=2.0,
        lat=3.0,
        alt=4.0,
        num_sats=5,
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
        point_storage = GPS_Cache()

        point_storage.storage_update.connect(self.receive_point)

        point_storage.store_info(self.mock_gps_point_1)

        assert (point_storage.StorageUpdateType.ADD, self.mock_gps_point_1) == self.received_point
        assert [self.mock_gps_point_1] == point_storage.get_gps_points()

    def test_storage_remove(self):
        point_storage = GPS_Cache()

        point_storage.storage_update.connect(self.receive_point)
        
        point_storage.store_info(self.mock_gps_point_1)

        point_storage.store_info(self.mock_gps_point_2)

        point_storage.remove_info(self.mock_gps_point_2)

        assert (point_storage.StorageUpdateType.REMOVE, self.mock_gps_point_2) == self.received_point
        assert [self.mock_gps_point_1] == point_storage.get_gps_points()

    def test_storage_clear(self):
        point_storage = GPS_Cache()

        point_storage.storage_update.connect(self.receive_point)

        point_storage.store_info(self.mock_gps_point_1)
        point_storage.store_info(self.mock_gps_point_2)

        point_storage.clear_points()

        assert (point_storage.StorageUpdateType.CLEAR, None) == self.received_point
        assert [] == point_storage.get_gps_points()
