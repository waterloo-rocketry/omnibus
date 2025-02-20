from enum import Enum

ONLINE_MODE: bool = False
TERMINAL_QR_CODE: bool = False
HTTP_SERVER_PORT: int = 8000
ZOOM_MAX: int = 30
ZOOM_MIN: int = 1

GRADIENT_COLORS: list[str] = [
    "#FF0000",  # Red
    "#FF4000",  # Orange-Red
    "#FF8000",  # Orange
    "#FFBF00",  # Yellow-Orange
    "#FFFF00",  # Yellow
    "#BFFF00",  # Yellow-Green
    "#80FF00",  # Green-Yellow
    "#40FF00",  # Green
    "#00FF00",  # Lime
    "#00FF40",  # Lime-Green
    "#00FF80",  # Spring-Green
    "#00FFBF",  # Aqua-Green
    "#00FFFF",  # Aqua
    "#00BFFF",  # Aqua-Blue
    "#0080FF",  # Dodger-Blue
    "#0040FF",  # Blue
    "#0000FF",  # Blue
    "#4000FF",  # Blue-Violet
    "#8000FF",  # Violet
    "#BF00FF",  # Magenta
    "#FF00FF",  # Magenta
    "#FF00BF",  # Deep-Pink
    "#FF0080",  # Hot-Pink
    "#FF0040",  # Pink
    "#FF0000"   # Red
]

class BoardID(Enum):
    GPS_BOARD: str = "GPS Board"
    PROCESSOR_BOARD: str = "Processor Board"

# # Example use of BoardID
# def get_board_description(board_id: BoardID) -> str:
#     if board_id == BoardID.GPS_BOARD:
#         return "This is the GPS Board used for location tracking."
#     elif board_id == BoardID.PROCESSOR_BOARD:
#         return "This is the Processor Board used for data processing."
#     else:
#         return "Unknown Board"

# # Example usage
# selected_board = BoardID.GPS_BOARD
# print(f"Selected Board: {selected_board.value}")
# print(get_board_description(selected_board))