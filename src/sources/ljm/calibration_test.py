import pytest

from calibration import Connection, LinearCalibration, Sensor, ThermistorCalibration


class TestLinearCalibration:
    def test_const_zero(self):
        c = LinearCalibration(0, 0, "unit")
        assert c.calibrate(0) == 0
        assert c.calibrate(-10) == 0
        assert c.calibrate(15) == 0

    def test_const_offset(self):
        c = LinearCalibration(0, 25, "unit")
        assert c.calibrate(0) == 25
        assert c.calibrate(-10) == 25
        assert c.calibrate(15) == 25

    def test_slope_zero(self):
        c = LinearCalibration(5, 0, "unit")
        assert c.calibrate(0) == 0
        assert c.calibrate(-10) == -50
        assert c.calibrate(15) == 75

    def test_slope_offset(self):
        c = LinearCalibration(5, 3, "unit")
        assert c.calibrate(0) == 3
        assert c.calibrate(-10) == -47
        assert c.calibrate(15) == 78


class TestThermistorCalibration:
    def test_thermistor(self):
        c = ThermistorCalibration(5, 10000, 3434, 0.099524)
        assert c.calibrate(5) == 0
        assert c.calibrate(4) == pytest.approx(65.8, 0.1)
        assert c.calibrate(3) == pytest.approx(35.9, 0.1)
        assert c.calibrate(2) == pytest.approx(14.9, 0.1)
        assert c.calibrate(1) == pytest.approx(-7, 0.1)


class TestSensorParser:
    def test_parsing(self):
        _ = Sensor(
            "Test", "TEST", 10, Connection.SINGLE, LinearCalibration(5, 0, "units")
        )
        parsed = Sensor.parse([[1, 2, 3, 4, 5]])
        assert "Test (units)" in parsed
        assert parsed["Test (units)"] == [5, 10, 15, 20, 25]
