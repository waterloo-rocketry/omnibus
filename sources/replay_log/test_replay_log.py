import pytest
import time
import string
import random

import msgpack

import replay_log as ReplayLogSource
import replay_log_test_sink as ReplayLogTestSink

TEST_LOG_IN = "./sources/replay_log/test_log_in.log"
TEST_LOG_OUT = "./sources/replay_log/test_log_out.log"


class TestReplayLog:
    def test_replay_consistency(self):
        self.generate_test_log()
        ReplayLogTestSink.log_test_logs()
        ReplayLogSource.replay(TEST_LOG_IN, 1)
        assert self.logs_match(TEST_LOG_IN, TEST_LOG_OUT)

    def test_replay_speed(self):
        pass
    
    def time_replay(self):
        pass

  
    def logs_match(self, in_log, out_log):
        with open(in_log, "rb") as f1: 
            with open(out_log, "rb") as f2: 
                unpacker1 = msgpack.Unpacker(file_like=f1)
                unpacker2 = msgpack.Unpacker(file_like=f2)
                while True: 
                    msg1 = ReplayLogSource.fetch_message(unpacker1) 
                    msg2 = ReplayLogSource.fetch_message(unpacker2) 
                    if msg1 != msg2: 
                        return False
                    if msg1 == None and msg2 == None:
                        return True
    

    def generate_test_log(self):
        with open(TEST_LOG_IN, "wb") as f:
            for i in range(200):
                f.write(msgpack.packb([self.rand_str(), time.time(), self.rand_str(100)]))
    
    def rand_str(self, l=10):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=l))




