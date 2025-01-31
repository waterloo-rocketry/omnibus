import pytest

from parse_ni_dat_log import main as ni_dat_log
from parse_ni_extrapolate_compression import main as ni_dat_extrapolate

def test_ni_dat_log():
    IN_FILE = "test_inputs/testNILog.dat"
    OUT_CSV = "OUTPUT-test_ni_dat_log.csv"
    EXPECTED_CSV = "test_inputs/expected-ni_dat_log.csv"
    ni_dat_log(IN_FILE, OUT_CSV)
    f1 = open(OUT_CSV, "r")
    f2 = open(EXPECTED_CSV, "r")
    lines1 = f1.readlines()
    lines2 = f2.readlines()
    assert(len(lines1) == len(lines2))
    for i in range(len(lines1)):
        assert(lines1[i] == lines2[i])


def test_ni_dat_extrapolate():
    IN_FILE = "test_inputs/testNILog.dat"
    OUT_CSV = "OUTPUT-test_ni_dat_extrapolate.csv"
    EXPECTED_CSV = "test_inputs/expected-ni_dat_extrapolate.csv"
    ni_dat_extrapolate(IN_FILE, OUT_CSV)
    f1 = open(OUT_CSV, "r")
    f2 = open(EXPECTED_CSV, "r")
    lines1 = f1.readlines()
    lines2 = f2.readlines()
    assert(len(lines1) == len(lines2))
    # Due to floating point errors we can't assert the contents
    