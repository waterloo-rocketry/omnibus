#TODO: This is on developed code not work functionally. 
import requests
import math
from mbtiles import MBtiles

def download_tile(url, z, x, y):
    """Download a single tile from a URL."""
    response = requests.get(url.format(z=z, x=x, y=y))
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to download tile: {url} (status code: {response.status_code})")

def deg2num(lat_deg, lon_deg, zoom):
    """Convert latitude/longitude to tile numbers."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def download_tiles_for_area(mbtiles_file, lat_min, lon_min, lat_max, lon_max, min_zoom, max_zoom, tile_url):
    """Download tiles for a specific area and save them to an MBTiles file."""
    mbtiles = MBtiles(mbtiles_file)
    mbtiles.init_mbtiles()  # Initialize the MBTiles database

    for zoom in range(min_zoom, max_zoom + 1):
        x_start, y_start = deg2num(lat_min, lon_min, zoom)
        x_end, y_end = deg2num(lat_max, lon_max, zoom)

        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                try:
                    tile_data = download_tile(tile_url, zoom, x, y)
                    mbtiles.add_tile(zoom, x, y, tile_data)  # Add tile to MBTiles
                    print(f"Downloaded tile Z{zoom} X{x} Y{y}")
                except Exception as e:
                    print(f"Error downloading tile Z{zoom} X{x} Y{y}: {e}")

    mbtiles.close()

if __name__ == "__main__":
    # Define the area and zoom levels for tile download
    lat_min, lon_min = 43.4, -80.6  # Bottom-left corner (Waterloo, ON)
    lat_max, lon_max = 43.5, -80.4  # Top-right corner
    min_zoom = 12
    max_zoom = 15

    # OpenStreetMap tile URL pattern
    tile_url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

    # Output MBTiles file
    mbtiles_file = "waterloo_tiles.mbtiles"

    # Start downloading tiles and saving them to MBTiles
    download_tiles_for_area(mbtiles_file, lat_min, lon_min, lat_max, lon_max, min_zoom, max_zoom, tile_url)
