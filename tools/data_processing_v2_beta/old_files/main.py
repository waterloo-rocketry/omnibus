# Data Processing v2 (beta) - Waterloo Rocketry

from processors import DAQDataProcessor

GLOBAL_LOG_FILE = "2025_05_05-05_41_50_PM.log"
CHANNEL = "DAQ/Fake"
OUTPUT_CSV_FILE = "output_v1.csv"


# TODO: Make this an actual app and not a script (and maybe GUI?)
def main() -> None:
    with open(GLOBAL_LOG_FILE, "rb") as file:
        processor = DAQDataProcessor(file, CHANNEL)
        processor.process()
        processor.csv_ify(OUTPUT_CSV_FILE)


if __name__ == "__main__":
    main()
