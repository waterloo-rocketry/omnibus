import io
import time
import string
import random

import msgpack
import pytest

import replay_log
from omnibus import Sender


def get_rand_str(l=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=l))


def get_percent_error(expected, received):
    return abs(expected - received) / expected


def bind_mock_send(mock_file):
    def mock_send(self, msg):
        if msg is None:
            return
        packed_bytes = msgpack.packb([msg.channel, msg.timestamp, msg.payload])
        mock_file.write(packed_bytes)
    return mock_send


def generate_mock_writetimes(size, max_incr):
    last = time.time()
    for _ in range(size):
        yield last
        last += max_incr * random.random()


class TestReplayLog:
    @pytest.fixture
    def mock_sender(self, monkeypatch):
        mock_file = io.BytesIO()
        monkeypatch.setattr(
            Sender,
            'send_message',
            bind_mock_send(mock_file)
        )
        monkeypatch.setattr(
            Sender,
            '__init__',
            lambda _: None
        )
        return mock_file

    @pytest.fixture
    def mock_input(self):
        INPUT_LENGTH = 50
        mocked_input = io.BytesIO()
        for wtime in generate_mock_writetimes(INPUT_LENGTH, 0.01):
            packed_bytes = msgpack.packb([get_rand_str(), wtime, get_rand_str(100)])
            mocked_input.write(packed_bytes)
        mocked_input.seek(0)
        yield mocked_input
        mocked_input.close()

    @pytest.mark.parametrize("replay_speed", [1, 3])
    def test_replay_output(self, mock_sender, mock_input, replay_speed):
        replay_log.replay(mock_input, replay_speed)
        assert mock_sender.getvalue() == mock_input.getvalue()

    def test_live_replay_speed(self, mock_sender, mock_input):
        replay_times = [1, 4, 0.25]
        runtimes = []
        for replay_time in replay_times:
            start = time.time()
            replay_log.replay(mock_input, replay_time)
            end = time.time()
            runtimes.append(end - start)
            mock_input.seek(0)
        for i, duration in enumerate(runtimes[1:]):
            expected_runtime = duration * replay_times[i + 1] / replay_times[0]
            percent_error = get_percent_error(runtimes[0], expected_runtime)
            assert percent_error < 0.10
