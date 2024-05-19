from pathlib import Path
from datetime import datetime
import argparse
import os
import sys

import replay_log

GLOBAL_LOGS = Path("../..")


def parse_arguments() -> argparse.Namespace:
    """
    Parses command line arguments.
    """
    def valid_replay_speed(n):
        n = float(n)
        if n <= 0:
            print(f"Error: replay speed must be greater than zero.")
            sys.exit(1)
        return n

    parser = argparse.ArgumentParser(prog="PROG")
    parser.add_argument('--replay_speed', '-r', default=1, type=valid_replay_speed,
                        help="replay speed of log, must be greater than zero (default: 1)")
    parser.add_argument('--max_logs', '-m', default=10, type=int,
                        help='number of logs files to display (default: 10)')
    parser.add_argument('log_file', nargs="?", default=None,
                        help="relative path to a log file (default: selection from prompt)")
    return parser.parse_args()


def get_replay_log(max_logs: int) -> Path | None:
    """
    Have the user select a log to replay. 
    """

    log_files = GLOBAL_LOGS.glob('*.log')
    # sort files by date last modified, newest to oldest
    log_files = sorted(log_files, key=os.path.getmtime)[::-1]
    log_files = log_files[:max_logs]

    if len(log_files) == 0:
        return None

    print(f"(R): Most recent")
    for option, log_file in enumerate(log_files):
        print(f"({option}): {log_file}")

    while selection := input("Input the log to repeat (no brackets): "):
        if selection == 'R' or (selection.isdigit() and 0 <= int(selection) < len(log_files)):
            selection = 0 if selection == 'R' else int(selection)
            break
        else:
            print("Invalid selection.")

    return log_files[selection]


if __name__ == "__main__":
    args = parse_arguments()
    max_logs = args.max_logs
    replay_speed = args.replay_speed
    log_file = args.log_file if args.log_file != None else get_replay_log(max_logs)

    if log_file == None:
        print("Error: unable to retrieve log file.")
        sys.exit(1)

    print(f"replaying log: {log_file}")
    print(f"replay speed: {replay_speed}x")

    with open(log_file, 'rb') as f:
        replay_log.replay(f, replay_speed)
