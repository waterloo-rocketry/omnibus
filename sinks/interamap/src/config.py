from enum import Enum

ONLINE_MODE: bool = True
MBTILES_PATH: str = "ontario-latest.osm.mbtiles"

TERMINAL_QR_CODE: bool = False
HTTP_SERVER_PORT: int = 8000
ZOOM_MAX: int = 30
ZOOM_MIN: int = 1
ZOOM_DEFAULT: int = 15

GRADIENT_COLORS: list[str] = [
    "#FF0000",  # Red
    "#FF8000",  # Orange
    "#FFFF00",  # Yellow
    "#80FF00",  # Green-Yellow
    "#00FF40",  # Lime-Green
    "#00FFBF",  # Aqua-Green
    "#00BFFF",  # Aqua-Blue
    "#0080FF",  # Dodger-Blue
    "#4000FF",  # Blue-Violet
    "#8000FF",  # Violet
]

class BoardID(Enum):
    GPS_BOARD = "GPS"
    PROCESSOR_BOARD = "PROCESSOR"

BOARD_FIELDS: dict[str, list[str]] = {
    BoardID.GPS_BOARD.value: ["GPS_INFO", "GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"],
    BoardID.PROCESSOR_BOARD.value: ["GPS_INFO", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]
}