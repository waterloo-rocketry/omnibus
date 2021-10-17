from pathlib import Path
from datetime import datetime
import argparse
import os

import replay_log as ReplayLogSource

GLOBAL_LOGS = "../../sinks/globallog/"


def parse_arguments():
    """
    Parses command line arguments.
    """
    parser = argparse.ArgumentParser(prog="PROG")
    parser.add_argument('--log_file', '-l', default=None,
                        help="relative path to a log file (default: selection from prompt)")
    parser.add_argument('--replay_speed', '-r', default=1, type=int,
                        help="replay speed of log (default: 1)")
    parser.add_argument('--max_logs', '-m', default=10, type=int,
                        help='number of logs files to display (default: 10)')
    args = parser.parse_args()
    return args


def get_replay_log(max_logs):
    """
    Have the user select a log to replay. Defaults to
    requesting the most recent log.
    """
    log_files = Path(GLOBAL_LOGS).glob('*.log')
    # sort files by datetime, newest to oldest
    log_files = sorted(log_files, key=get_datetime)[::-1]

    log_files = log_files[:max_logs]

    if len(log_files) == 0:
        return None # no global logs to replay 
    
    print(f"(R): Most recent")
    for option, log_file in enumerate(log_files):
        print(f"({option}): {log_file}")

    selection = input("Input the log to repeat (no brackets): ")
    if selection == 'R':
        selection = 0  # most recent
    else:
        try:
            selection = int(selection)
            if selection < 0 or selection >= len(log_files):
                raise IndexError("Invalid index for selection")
        except:
            print("Error: invalid selection. Showing most recent log.")
            selection = 0

    return os.path.join(GLOBAL_LOGS, log_files[selection])


def get_datetime(filename):
    """
    Assumes file was produced by globallog/main.py.
    Produces datatime object for filename.
    """
    f_datetime = Path(filename).stem
    datetime_obj = datetime.strptime(f_datetime, "%Y_%m_%d-%I_%M_%S_%p")
    return datetime_obj


if __name__ == "__main__":
    args = parse_arguments()
    MAX_LOGS = args.max_logs
    REPLAY_SPEED = args.replay_speed if args.replay_speed > 0 else 1
    LOG_FILE = args.log_file if args.log_file != None else get_replay_log(MAX_LOGS)

    ReplayLogSource.replay(LOG_FILE, REPLAY_SPEED)
