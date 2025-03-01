# Data Processing v2 (beta) - Waterloo Rocketry

from processors import DAQDataProcessor

GLOBAL_LOG_FILE = "[PATH HERE]"
CHANNEL = "DAQ"
OUTPUT_CSV_FILE = "[PATH HERE]"


# TODO: Make this an actual app and not a script (and maybe GUI?)
def main() -> None:
    with open(GLOBAL_LOG_FILE, "rb") as file:
        processor = DAQDataProcessor(file, CHANNEL)
        processor.process()
        processor.csv_ify(OUTPUT_CSV_FILE)


if __name__ == "__main__":
    main()
