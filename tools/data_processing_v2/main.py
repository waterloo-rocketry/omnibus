
from daq_processing.daq_processing import DAQDataProcessor

def main():
    with open("2025_03_01-02_14_03_AM.log", "rb") as file:
        processor = DAQDataProcessor(file, "DAQ/Fake")
        processor.process()
        processor.csv_ify("test.csv")


if __name__ == "__main__":
    main()