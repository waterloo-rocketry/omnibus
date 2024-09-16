#TODO: This is on developed code not work functionally. 
# data_downloader.py

import os
import requests
import zipfile
from tqdm import tqdm

NATURAL_EARTH_URLS = {
    'land': 'https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_land.zip',
    'borders': 'http://www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_boundary_lines_land.zip',
    # Add other shapefiles as needed
}

def download_shapefiles(shapefile_dir):
    """
    Checks for required shapefiles and downloads them if they are missing.
    """
    os.makedirs(shapefile_dir, exist_ok=True)

    for name, url in NATURAL_EARTH_URLS.items():
        zip_filename = os.path.join(shapefile_dir, f'{name}.zip')
        shp_filename = os.path.join(shapefile_dir, f'ne_110m_{name}.shp')

        if not os.path.exists(shp_filename):
            print(f'Downloading {name} shapefile...')
            download_file(url, zip_filename)
            print(f'Extracting {zip_filename}...')
            extract_zip(zip_filename, shapefile_dir)
            os.remove(zip_filename)
        else:
            print(f'{name} shapefile already exists.')

def download_file(url, dest_path):
    """
    Downloads a file from the given URL to the specified destination path.
    """
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    with open(dest_path, 'wb') as file, tqdm(
        desc=dest_path,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

def extract_zip(zip_path, extract_to):
    """
    Extracts a zip file to the specified directory.
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
