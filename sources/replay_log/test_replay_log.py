import time
import os
import string
import random

import msgpack
import pytest

import replay_log as ReplayLogSource
from omnibus import Sender

TEST_LOG_IN = "./sources/replay_log/test_log_in.log"
TEST_LOG_OUT = "./sources/replay_log/test_log_out.log"

class TestReplayLog:
    @pytest.fixture
    def sender(self, mocker):
       mocker.patch.object(
            Sender,
            'send_message',
            new=mock_send_message
       ) 
    
    @pytest.fixture
    def input_log(self):
        # create input log file 
        with open(TEST_LOG_IN, "wb") as f:
            last_time = time.time()
            for i in range(50):
                f.write(msgpack.packb([rand_str(), last_time, rand_str(100)])) 
                # randomly add 0-0.01s of delay
                last_time += random.randint(0, 10) * (1 / 1000)

        yield

        # destroy test files
        os.remove(TEST_LOG_IN)
        os.remove(TEST_LOG_OUT)
        
    def test_replay_consistency(self, input_log, sender):
        ReplayLogSource.replay(TEST_LOG_IN, 1)
        assert logs_match(TEST_LOG_IN, TEST_LOG_OUT)

    def test_replay_consistency_w_speed_change(self, input_log, sender):
        ReplayLogSource.replay(TEST_LOG_IN, 3)
        assert logs_match(TEST_LOG_IN, TEST_LOG_OUT)

    def test_replay_speed_increase(self, input_log, sender):
        s1 = time.time()
        ReplayLogSource.replay(TEST_LOG_IN, 1)
        t1 = time.time() - s1

        s2 = time.time()
        ReplayLogSource.replay(TEST_LOG_IN, 4)
        t2 = time.time() - s2

        # timing is not very percise, 4x speed should be at least 2x faster
        assert t2 <= t1 / 2

    def test_replay_speed_decrease(self, input_log, sender):
        s1 = time.time()
        ReplayLogSource.replay(TEST_LOG_IN, 1)
        t1 = time.time() - s1

        s2 = time.time()
        ReplayLogSource.replay(TEST_LOG_IN, 0.25)
        t2 = time.time() - s2

        # timing is not very percise, a quarter to speed should be at least half as fast 
        assert t2 >= t1 * 2
    
   
# replaces Sender.send_message
def mock_send_message(self, message):
    mock_receive_message(message)

# mocks the receipt of a message
def mock_receive_message(msg):
    if msg == None:
        return
    with open(TEST_LOG_OUT, "ab") as f:
        f.write(msgpack.packb([msg.channel, msg.timestamp, msg.payload]))

def logs_match(in_log, out_log):
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

def rand_str(l=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=l))
