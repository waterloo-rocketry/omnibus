# Replay Log: Replays previous logs from the Global Log sink 
from omnibus import Sender;
import os
from datetime import datetime

sender = Sender()
CHANNEL = ""

logs_path = "../../sinks/globallog/"

def retreive_log_files():
  log_files = [file for file in os.list_dir(logs_path) if file.contains(".log")]
  return log_files

def parse_filename_datetime(filename):
  """
  Assumes file was produced by globallog/main.py.
  Produces datatime object for filename.
  """
  f_datetime = filename.split(".")[0]
  datetime_obj = datetime.strptime(f_datetime, "%Y_%m_%d-%I_%M_%S_%p")
  return datetime_obj

# TODO: make max_log_files a commandline argument 
def get_replay_log(max_log_files=10):
  """
  Have the user select a log to replay. Defaults to
  requesting the most recent log.
  """
  log_files = retreive_log_files()
  # sort files by datetime, newest to oldest
  log_files = sorted(log_files, key=parse_filename_datetime)[::-1]

  log_files = log_files[:max_log_files]

  for option, log_file in enumerate(log_files):
    print(f"({option}): {log_file}")
  print(f"(R): Most recent")

  selection = input("Input the log to repeat (no brackets): ")
  if selection == 'R':
    selection = 0 # most recent
  else:
    try:
      selection = int(selection)
      if selection < 0 or selection >= len(log_files):
        raise IndexError("Invalid index for selection") 
    except (e): 
      print("Error: invalid selection. Showing most recent log.")
      selection = 0
  
  return log_files[selection]

def replay_log(log_file):
  """
  Replays the contents of a log_file.
  """
  pass

if __name__ == "__main__":
  replay_log_file = get_replay_log()
  replay_log(replay_log_file)
