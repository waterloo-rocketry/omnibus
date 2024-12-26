import zipfile
from fastkml import kml

from src.data_struct import Point_GPS, LineString_GPS


class KMZParser:
    def __init__(self, kmz_file_path):
        self.kmz_file_path = kmz_file_path
        self.kml_obj = self.parse_kmz()
        self.gps_data = []
        self.parse_kml_features(self.kml_obj)

    def parse_kmz(self):
        with zipfile.ZipFile(self.kmz_file_path, "r") as kmz:
            # List all files in the KMZ archive
            kml_files = [f for f in kmz.namelist() if f.endswith(".kml")]

            if not kml_files:
                raise FileNotFoundError("No KML file found in the KMZ archive.")

            # Use the first KML file found
            kml_file_name = kml_files[0]
            with kmz.open(kml_file_name, "r") as kml_file:
                k = kml.KML().parse(kml_file)

        print(k.to_string())
        return k

    def parse_kml_features(self, kml_obj):
        """Display the KML features on the map."""
        for feature in list(kml_obj.features):
            if hasattr(feature, "geometry") and feature.geometry:
                self.gps_data.append(self.parse_detail_geometry(feature))
            if hasattr(feature, "features"):
                self.parse_kml_features(feature)

    def parse_detail_geometry(self, feature):
        geom = feature.geometry
        geom_type = geom.geom_type
        timestamp = ( # point will never have a timestamp, only Placemark will
            getattr(feature, "name", "")
            if (type(feature).__name__ == "Placemark")
            else None
        )
        if geom_type == "Point":
            lon, lat, alt = geom.coords[0]
            return Point_GPS(lon, lat, alt, 0, time_stamp=timestamp) # unsure what num_sats is
        elif geom_type == "LineString":
            linestring = LineString_GPS()
            coords = [coord[:3] for coord in geom.coords]  # Extract lon and lat
            for coord in coords:
                linestring.add_point(Point_GPS(coord[0], coord[1], coord[2], timestamp))
            return linestring
        else:
            print(f"Unhandled geometry type: {geom_type}")