### Interamap - A sink for omnibus systems

To start the Interamap, run the following command (Currently, on develop stage):

```bash
cd interamap
pip install -r requirements.txt
python main.py
```
### <font color="Yellow"> Make sure you are in the `interamap` directory before running the command. </font>

### Offline Usage

Requirements:
- [Tileserver](https://tileserver.readthedocs.io/en/latest/installation.html)
- [Mbtiles Data](https://drive.google.com/drive/folders/1nIU1vqQJ2A0i9TZeG5T14Rajfa-ljGfe?usp=sharing)
- [Tilemaker](https://github.com/systemed/tilemaker) (Optional)

**For offline usage, you need to download the tiles required**
1.  - **Option 1:** [Rocketry Team Tiles Folder](https://drive.google.com/drive/folders/1nIU1vqQJ2A0i9TZeG5T14Rajfa-ljGfe?usp=sharing) 
    
        Download `.mbtiles` files, and place it under `resources/mbtiles` folder
    
        (For any other offline area required, connect with me on slack)

    - **Option 2:** Download the pbf file from
     [OpenStreetMap](https://download.geofabrik.de/north-america/canada.html) (For all area)
     
        This will give you pbf files for the country(area) you want to use, you need to convert them to mbtiles with [tilemaker](https://github.com/systemed/tilemaker)

        After you get the mbtiles file, place it under `resources/mbtiles` folder

        (Note: tilemaker don't have a compiled distribution (At least for MacOS), you need to compile it yourself)  

        (Side: For MacOS, check about this [issue](https://github.com/systemed/tilemaker/issues/690), for dependencies error)
2. Run the following command to start tileserver:
    ```bash
    python -m tileserver "ontario-latest.osm.mbtiles" 
    ```
    (Make sure you installed the tileserver follow this [instructions](https://tileserver.readthedocs.io/en/latest/installation.html))

3. Edit the `config.py` file to change the `offline` variable to `True`
4. Run the following command to start the Interamap:
    ```bash
    python main.py
    ```
    (Note: For offline mode, dark mode is not available)