import zipfile
from fastkml import kml

def parse_kmz(kmz_file_path):
    with zipfile.ZipFile(kmz_file_path, 'r') as kmz:
        # List all files in the KMZ archive
        kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
        
        if not kml_files:
            raise FileNotFoundError('No KML file found in the KMZ archive.')
        
        # Use the first KML file found
        kml_file_name = kml_files[0]
        with kmz.open(kml_file_name, 'r') as kml_file:
            kml_content = kml_file.read()
    k = kml.KML()
    k.from_string(kml_content)
    return k

def print_detail_geometry(geom, feature):
        geom_type = geom.geom_type
        if geom_type == 'Point':
            lon, lat, he = geom.coords[0]
            print(f'Point: {lon}, {lat}, {he}')
        elif geom_type == 'LineString':
            coords = [coord[:2] for coord in geom.coords]  # Extract lon and lat
            lons, lats = zip(*coords)
            print(f'LineString: {lons}, {lats}')
        elif geom_type == 'Polygon':
            print(f'Polygon: {geom.exterior.coords[:2]}')
        elif geom_type in ['MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection']:
            for part in geom.geoms:
                print_detail_geometry(part, feature)
        else:
            print(f'Unhandled geometry type: {geom_type}')

def print_kml_structure(kml_obj, indent=0):
    for feature in kml_obj.features():
        print('  ' * indent + f'{type(feature).__name__}: {getattr(feature, "name", "")}')
        if hasattr(feature, 'geometry') and feature.geometry:
            print('  ' * (indent + 1) + f'Geometry: ', end='')
            print_detail_geometry(feature.geometry, feature)
        if hasattr(feature, 'features'):
            print_kml_structure(feature, indent + 1)

            
if __name__ == '__main__':
    kmz_file_path = 'data/kmz_files/Borealis LC 2024 Processor.kmz'
    kml_obj = parse_kmz(kmz_file_path)
    print_kml_structure(kml_obj)