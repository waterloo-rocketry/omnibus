## Interamap - A sink for omnibus systems

To launch the interamap map, follow the instructions below:

---------

### Make sure you are in the `interamap` directory before running the command!!!

- ### Online Usage
    ```bash
    pip install -r requirements.txt
    python main.py
    ```


- ### Offline Usage
    Requirements:
    - [Docker](https://www.docker.com/get-started)

        (Note: Docker is used because Tileserver GL is unstable and has limited support on Windows and MacOS. Running Tileserver GL in a Docker container improves reliability and compatibility.)
    - [Mbtiles Data](https://drive.google.com/drive/folders/1nIU1vqQJ2A0i9TZeG5T14Rajfa-ljGfe?usp=sharing)
    - [Tilemaker](https://github.com/systemed/tilemaker) (Optional)
    
    **For offline usage, you need to download the tiles required**
    1.  - **Option 1:** [Rocketry Team Tiles Folder](https://drive.google.com/drive/folders/1nIU1vqQJ2A0i9TZeG5T14Rajfa-ljGfe?usp=sharing) 
        
            Download `ontario-latest.osm.mbtiles` files, and place it under `resources/mbtiles` folder
        
            (For any other offline area required, ping with me (Jiucheng) on slack)
    
        - **Option 2:** Download the pbf file from
         [OpenStreetMap](https://download.geofabrik.de/north-america/canada.html) (For all area)
         
            This will give you pbf files for the country(area) you want to use, you need to convert them to mbtiles with [tilemaker](https://github.com/systemed/tilemaker)
    
            After you get the mbtiles file, place it under `resources/mbtiles` folder
    
            (Note: tilemaker don't have a compiled distribution (At least for MacOS), you need to compile it yourself)  
    
            (Side: For MacOS, check about this [issue](https://github.com/systemed/tilemaker/issues/690), for dependencies error)
    2. Edit the `sinks/interamap/config.py` file to change the `ONLINE_MODE` flag to `False` 
    3. Run the following command to start the Interamap:

        ```bash
        python sinks/interamap/main.py
        ```
        (Note: For offline mode, dark mode map is not available)
    4. Run the following command to manually start the tileserver: (This is optional, only use if tileserver is not started automatically)

        ```bash
        cd sinks/interamap

        # Make sure docker is running
        python tileserver.py start 

        # If you want to stop the tileserver, run:
        python tileserver.py stop
        ```
