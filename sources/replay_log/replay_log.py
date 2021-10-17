"""
Replay Log Source
-  
Replays previous logs from the Global Log sink,
or from a selected file, in real time.

See python3 main.py --help for options.
"""

from omnibus import Sender, Message
import time
import os
import msgpack
from datetime import datetime
import argparse


class ReplayLog:
    GLOBAL_LOGS = "../../sinks/globallog/"

    def __init__(self):
        args = self.parse_arguments()
        self.MAX_LOGS = args.max_logs
        self.REPLAY_SPEED = max(1, args.replay_speed)
        self.LOG_FILE = args.log_file

        if self.LOG_FILE == None:
            self.LOG_FILE = self.get_replay_log(self.MAX_LOGS)

    def replay_selected_log(self):
        """
        Replays the contents of a log_file.
        """

        log_msgs = self.unpack_log(self.LOG_FILE)
        r_start_time = time.time()  # real time
        l_start_time = log_msgs[0].timestamp  # log time

        sender = Sender()
        for message in log_msgs:
            r_time = time.time()
            l_time = message.timestamp

            delta_r_time = (r_time - r_start_time) * self.REPLAY_SPEED
            delta_l_time = l_time - l_start_time

            # wait for the real time to catch up to the delta time
            wait_time = max(0, delta_l_time - delta_r_time)
            time.sleep(wait_time)

            """
      Note that we use send_message() over send() here, 
      keeping the old timestamp, message.timestamp.
      """
            sender.send_message(message)

    def parse_arguments(self):
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

    def get_replay_log(self, max_logs):
        """
        Have the user select a log to replay. Defaults to
        requesting the most recent log.
        """
        log_files = self.get_global_log_files()
        # sort files by datetime, newest to oldest
        log_files = sorted(log_files, key=self.get_datetime)[::-1]

        log_files = log_files[:max_logs]

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

        return os.path.join(self.GLOBAL_LOGS, log_files[selection])

    def unpack_log(self, log_file):
        """
        Retreives list of message objects from a log_file.
        """
        logs = []
        with open(log_file, 'rb') as f:
            unpacker = msgpack.Unpacker(file_like=f)

            try:
                while True:
                    logs.append(unpacker.unpack())
            except msgpack.exceptions.OutOfData as e:
                pass

            f.close()
        logs = [Message(channel, timestamp, payload) for channel, timestamp, payload in logs]

        return logs

    def get_global_log_files(self):
        return [file for file in os.listdir(self.GLOBAL_LOGS) if file.split(".")[-1] == "log"]

    def get_datetime(self, filename):
        """
        Assumes file was produced by globallog/main.py.
        Produces datatime object for filename.
        """
        f_datetime = filename.split(".")[0]
        datetime_obj = datetime.strptime(f_datetime, "%Y_%m_%d-%I_%M_%S_%p")
        return datetime_obj
