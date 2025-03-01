# Data Processing v2 (beta) - Waterloo Rocketry

from processors import DAQDataProcessor


# TODO: Make this an actual app and not a script (and maybe GUI?)
def main() -> None:
    with open("2025_03_01-02_14_03_AM.log", "rb") as file:
        processor = DAQDataProcessor(file, "DAQ/Fake")
        processor.process()
        processor.csv_ify("test.csv")


if __name__ == "__main__":
    main()
