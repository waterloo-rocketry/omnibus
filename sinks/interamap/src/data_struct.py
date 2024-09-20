from typing import List, Optional

class Point_GPS():
    def __init__(self, lon: float, lat: float, he: float, time_stamp: Optional[str] = None):
        self.time_stamp = time_stamp
        self.lon = lon
        self.lat = lat
        self.he = he

    def __str__(self):
        return f"Point: {self.lon}, {self.lat}, {self.he}, At {self.time_stamp}"


class LineString_GPS():
    def __init__(self, points: Optional[List[Point_GPS]] = None):
        self.points = points if points is not None else []

    def add_point(self, point: Point_GPS):
        self.points.append(point)

    def remove_point(self, index: int):
        self.points.pop(index)

    def __str__(self):
        return f"LineString: {self.points}"