# Data Processing Tool

A tool to extract meaninful data streams from DAQ and CAN channels from test or flight logs comming from globallogger.

## Usage

- Store the log file being extracted from in the top level of omnibus
- `python tools/data_processing/main.py <log_filename.log>` with the following arguments
  - One of:
    - `-p` to preview the data, selecting certain columns, and plotting them to find the timestamps of interrest
    - `-e` to export the data, selecting columns and time ranges, and saving them to CSVs
  - One of:
    - `-d` to only deal with DAQ data
    - `-c` to only deal with CAN data
    - `-a` to deal with both DAQ and CAN data
    - `-b` extract behind stream for can messages. This might be useufl if there were two sources of CAN data in the logs with conflicting timestamps. Ommiting this takes the forward stream, and putting it takes the behind stream.
- When choosing colums or timestamps, you can just leave them empty to get everything

For each export, the program will output CSVs with the datapoints for the selected collums between the selected times. It also exports a manifest for the settings used to do the export, and has a shared export hash.

## Notes

It's important to note for the CSV data exported, each value in a row represents the most up to date infromation at that point, and not neceresally a reading at that timestamp, which could have consequences of signal processing. To only get datapoints for the times there was a reading, export only that column.

The CAN collums being looked for have to be manually added to `can_field_definitions.py`'s  dictionary. You can run `field_peeking.py` to see the CAN and DAQ fields present in the log file given, and then add a field defintion with an insightful name, the signature from the field export, and the direction to the specific data point to be extracted (ex: data.value).

## Future changes needed

- We should find a solution for the ahead/behind CAN data streams by going off of the CAN timestamp rather than the msgpacked timestmap
  - See: https://waterloorocketry.slack.com/archives/C07MX0QDS/p1706481412008559?thread_ts=1706479899.045329&cid=C07MX0QDS
- Uncompressing DAQ data by potentially interpolating the multiple data points. Right now they are just agregated by taking the average of each message, but this signficantly reduces temporal resolution
