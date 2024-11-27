from enum import IntEnum

from PySide6.QtCore import QThread, Signal

from src.data_struct import Point_GPS, Info_GPS, LineString_GPS


class GPS_Cache(QThread):
    """
    Stores GPS points and emits a signal when the storage is updated.
    """
    storage_update = Signal(object)

    class StorageUpdateType(IntEnum):
        ADD = 0
        REMOVE = 1
        CLEAR = 2

    def __init__(self):
        QThread.__init__(self)
        self.gps_points = []
        self.gps_linestrings = []

    def store_info(self, info_stream):
        if isinstance(info_stream, Point_GPS):
            self.gps_points.append(info_stream)
        elif isinstance(info_stream, Info_GPS):
            # GPS Info is not stored, only display in stream on UI
            pass
        else:
            print("Unknown info type", info_stream)
            pass

        self.storage_update.emit((self.StorageUpdateType.ADD, info_stream))

    def store_infos(self, infos):
        """
        Store a list of points
        """
        for info in infos:
            self.store_info(info)

    def get_gps_points(self):
        return self.gps_points

    def get_linestring_gps(self):
        return self.gps_linestrings

    def clear_points(self):
        self.gps_points.clear()
        self.storage_update.emit((self.StorageUpdateType.CLEAR, None))
    
    def clear_linestrings(self):
        self.gps_linestrings.clear()
        self.storage_update.emit((self.StorageUpdateType.CLEAR, None))

    def remove_info(self, info):
        try:
            if isinstance(info, Point_GPS):
                self.gps_points.remove(info)
            elif isinstance(info, LineString_GPS):
                self.gps_linestrings.remove(info)
            else:
                print("Unknown info type", info)
                pass

            self.storage_update.emit((self.StorageUpdateType.REMOVE, info))
        except KeyError:
            raise "Error: Unstored info to be removed" + str(info)

    def __str__(self):
        string = ""
        string += "GPS Points:\n"
        for point in self.gps_points:
            string += str(point) + "\n"
            
        string += "\nGPS LineStrings:\n"
        for linestring in self.gps_linestrings:
            string += str(linestring) + "\n"
        return string