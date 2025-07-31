import zipfile
from datetime import datetime
from enum import IntEnum
import os

from PySide6.QtCore import QThread, Signal
from fastkml import kml, geometry, times

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
        self.setObjectName("GPS_Cache")
        self.gps_points = []
        self.gps_linestrings = []
        self.relative_path = os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))
        )

    def store_info(self, info_stream):
        if isinstance(info_stream, Point_GPS):
            self.gps_points.append(info_stream)
        elif isinstance(info_stream, Info_GPS):
            # GPS Info is not stored, only display in stream on UI
            pass
        elif isinstance(info_stream, LineString_GPS):
            self.gps_linestrings.append(info_stream)
        elif isinstance(info_stream, list):
            for info in info_stream:
                self.store_info(info)
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

    def export_points(self):
        """Export the map to KML file."""
        file_name = f"waterloo_rocketry_gps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.kmz"
        file_path = os.path.join(self.relative_path, "shared", file_name)
        gps_points_placemarks: dict[str, kml.Folder] = {}
        gps_linestring_placemarks = kml.Folder()

        # add points to placemarks
        for p in self.gps_points:
            if p.time_stamp and '.' not in p.time_stamp:
                p.time_stamp += '.0'

            time = datetime.combine(
                datetime.today(),
                datetime.strptime(p.time_stamp, '%H:%M:%S.%f').time()) if p.time_stamp else None

            if p.board_id not in gps_points_placemarks.keys():
                gps_points_placemarks[p.board_id] = kml.Folder(name=p.board_id)

            gps_points_placemarks[p.board_id].append(
                kml.Placemark(
                    name="GPS Point",
                    description=f"Time: {time} Board ID: {p.board_id}",
                    times=times.TimeStamp(timestamp=times.KmlDateTime(time)) if p.time_stamp else None,
                    kml_geometry=geometry.Point(
                        kml_coordinates=geometry.Coordinates(
                            coords=[(p.lon, p.lat, p.alt)]
                        )
                    )
                )
            )

        # add linestrings to placemarks
        for l in self.gps_linestrings:
            sample_point = l.points[0] # only points have timestamp/board_id so we grab the first one
            if sample_point.time_stamp and '.' not in sample_point.time_stamp:
                sample_point.time_stamp += '.0'

            time = datetime.combine(
                datetime.today(),
                datetime.strptime(p.time_stamp, '%H:%M:%S.%f').time()) if sample_point.time_stamp else None

            gps_linestring_placemarks.append(
                kml.Placemark(
                    name="GPS Linestring",
                    description=f"Time: {sample_point.time_stamp} Board ID: {sample_point.board_id}",
                    times=times.TimeStamp(timestamp=times.KmlDateTime(time)) if sample_point.time_stamp else None,
                    kml_geometry=geometry.LineString(
                        kml_coordinates=geometry.Coordinates(
                            coords=[(p.lon, p.lat, p.alt) for p in l.points]
                        )
                    )
                )
            )

        # Flatten Documents into one
        main_doc = kml.Document(name="Waterloo Rocketry GPS")
        for folder in gps_points_placemarks.values():
            main_doc.append(folder)
        main_doc.append(gps_linestring_placemarks)

        k = kml.KML(features=[main_doc])

        try:
            # k.write(pathlib.Path('points.kml'), prettyprint=True) # Debug: write directly as kml file
            with zipfile.ZipFile(file_path, "w") as kmz:
                kmz.writestr("doc.kml", k.to_string(prettyprint=True))
        except Exception as e:
            print(f"Error exporting points: {e}")

        print(f"Exported points to {file_path}")

    def __str__(self):
        string = ""
        string += "GPS Points:\n"
        for point in self.gps_points:
            string += str(point) + "\n"
            
        string += "\nGPS LineStrings:\n"
        for linestring in self.gps_linestrings:
            string += str(linestring) + "\n"
        return string