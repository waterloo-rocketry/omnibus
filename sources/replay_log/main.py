# Replay Log: Replays previous logs from the Global Log sink 
from omnibus import Sender;
import os
import msgpack
from datetime import datetime

# sender = Sender()
# CHANNEL = ""

LOGS = "../../sinks/globallog/"

def retreive_log_files():
  return [file for file in os.listdir(LOGS) if file.split(".")[-1] == "log"]

def get_datetime(filename):
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
  log_files = sorted(log_files, key=get_datetime)[::-1]

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
  
  return os.path.join(LOGS, log_files[selection])

def unpack_log(log_file):
  """
  Retreives list of message objects from a log_file.
  """
  logs = []
  with open(log_file, 'rb') as f:
    unpacker = msgpack.Unpacker(file_like=f)

    try:
      log = None
      while log := unpacker.unpack():
        logs.append(log)
    except msgpack.exceptions.OutOfData as e:
      pass
    
    f.close()
  for log in logs:
    print(log[1])
  
  return logs

def replay_log(log_file):
  """
  Replays the contents of a log_file.
  """

  unpack_log(log_file)
  # pass

if __name__ == "__main__":
  replay_log_file = get_replay_log()
  replay_log(replay_log_file)
