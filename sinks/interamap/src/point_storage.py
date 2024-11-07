from enum import IntEnum

from PySide6.QtCore import QThread, Signal

from src.data_struct import Point_GPS, LineString_GPS


class Point_Storage(QThread):
    """
    Stores GPS points and emits a signal when the storage is updated.
    """
    storage_update = Signal(object)

    class StorageUpdateType(IntEnum):
        ADD = 0
        REMOVE = 1
        CLEAR = 2

    def __init__(self, gps_RT_data: Signal):
        QThread.__init__(self)
        self.gps_points = []

        gps_RT_data.connect(self.store_point)

    def store_point(self, point):
        if isinstance(point, Point_GPS):
            self.gps_points.append(point)
        elif isinstance(point, LineString_GPS):
            pass  # to be implemented

        self.storage_update.emit((self.StorageUpdateType.ADD, point))

    def get_gps_points(self):
        return self.gps_points

    def get_linestring_gps(self):
        pass

    def clear_points(self):
        self.gps_points.clear()

        self.storage_update.emit((self.StorageUpdateType.CLEAR, None))

    def remove_point(self, point):
        try:
            if isinstance(point, Point_GPS):
                self.gps_points.remove(point)
            elif isinstance(point, LineString_GPS):
                pass

            self.storage_update.emit((self.StorageUpdateType.REMOVE, point))
        except KeyError:
            pass
