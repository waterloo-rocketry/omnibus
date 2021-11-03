import time
from filecmp import cmp
from contextlib import suppress
import os
import string
import random

import msgpack
import pytest

import replay_log 
from omnibus import Sender

TEST_LOG_IN = "./sources/replay_log/test_log_in.log"
TEST_LOG_OUT = "./sources/replay_log/test_log_out.log"


class TestReplayLog:
    @pytest.fixture
    def sender(self, monkeypatch):
        monkeypatch.setattr(
            Sender,
            'send_message',
            mock_send_message
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
        delete_file(TEST_LOG_IN)
        delete_file(TEST_LOG_OUT)

    def test_replay_consistency(self, input_log, sender):
        replay_log.replay(TEST_LOG_IN, 1)
        assert cmp(TEST_LOG_IN, TEST_LOG_OUT, shallow=False)

    def test_replay_consistency_w_speed_change(self, input_log, sender):
        replay_log.replay(TEST_LOG_IN, 3)
        assert cmp(TEST_LOG_IN, TEST_LOG_OUT, shallow=False)

    def test_replay_speed_increase(self, input_log, sender):
        s1 = time.time()
        replay_log.replay(TEST_LOG_IN, 1)
        t1 = time.time() - s1

        s2 = time.time()
        replay_log.replay(TEST_LOG_IN, 4)
        t2 = time.time() - s2

        # timing isn't perfect 
        assert t2 <= t1 / 3.9 

    def test_replay_speed_decrease(self, input_log, sender):
        s1 = time.time()
        replay_log.replay(TEST_LOG_IN, 1)
        t1 = time.time() - s1

        s2 = time.time()
        replay_log.replay(TEST_LOG_IN, 0.25)
        t2 = time.time() - s2

        # timing isn't perfect 
        assert t2 >= t1 * 3.9 


# replaces Sender.send_message
def mock_send_message(self, message):
    mock_receive_message(message)


# mocks the receipt of a message
def mock_receive_message(msg):
    if msg == None:
        return
    with open(TEST_LOG_OUT, "ab") as f:
        f.write(msgpack.packb([msg.channel, msg.timestamp, msg.payload]))


def rand_str(l=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=l))


def delete_file(f):
    with suppress(FileNotFoundError):
        os.remove(f)
