from typing import List, Optional

class Point_GPS():
    def __init__(self, lon: float, lat: float, alt: float, num_sats: int, time_stamp, board_id: Optional[str] = None):
        self.time_stamp = time_stamp
        self.num_sats = num_sats
        self.lon = lon
        self.lat = lat
        self.alt = alt
        self.board_id = board_id

    def __str__(self):
        return f"Point: {self.lat}, {self.lon}, {self.alt}, At {self.time_stamp}, With {self.num_sats} satellites, from {self.board_id}"

# Ignore, Currently not used
class LineString_GPS():
    def __init__(self, points: Optional[List[Point_GPS]] = None):
        self.points = points if points is not None else []

    def add_point(self, point: Point_GPS):
        self.points.append(point)

    def remove_point(self, index: int):
        self.points.pop(index)

    def __str__(self):
        return f"LineString: {self.points}"


class Info_GPS():
    def __init__(self, num_sats: int, quality: int, board_id: Optional[str] = None):
        self.num_sats = num_sats
        self.quality = quality
        self.board_id = board_id

    def __str__(self):
        return f"Info: {self.num_sats} satellites, Quality: {self.quality}, from {self.board_id}"