import io
import time
import string
import random

import msgpack
import pytest

import replay_log


def get_rand_str(l=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=l))


def get_percent_error(expected, received):
    return abs(expected - received) / expected


def generate_mock_writetimes(size, max_incr):
    last = time.time()
    for _ in range(size):
        yield last
        last += max_incr * random.random()


def get_runtime(func, *args, **kwargs):
    start = time.time()
    func(*args, **kwargs)
    end = time.time()
    return end - start


class MockSender:
    """class used to mock omnibus.Sender
    mocking ombnibus.Sender supresses constructor side effects
    and mocks send_message attribute
    """
    # mock file to record sent messages
    # has class scope to simplify monkeypatching
    mock_file = None

    def send_message(self, msg):
        if msg is None:
            return
        packed_bytes = msgpack.packb([msg.channel, msg.timestamp, msg.payload])
        self.mock_file.write(packed_bytes)


class TestReplayLog:
    @pytest.fixture
    def mock_sender(self, monkeypatch):
        """mock omnibus.Sender and return sender's mock_file
        """
        MockSender.mock_file = io.BytesIO()
        monkeypatch.setattr(
            replay_log,
            'Sender',
            MockSender
        )
        return MockSender.mock_file

    @pytest.fixture
    def mock_input(self):
        """manages and yields mock log stream
        mock log stream is first arg passed to replay_log.replay
        """
        INPUT_LENGTH = 50
        mocked_input = io.BytesIO()
        # generate random log
        # log content beyond format is irrelevant, so left unrestricted
        for wtime in generate_mock_writetimes(INPUT_LENGTH, 0.01):
            packed_bytes = msgpack.packb([get_rand_str(), wtime, get_rand_str(100)])
            mocked_input.write(packed_bytes)
        mocked_input.seek(0)
        yield mocked_input
        mocked_input.close()

    @pytest.mark.parametrize("replay_speed", [1, 0.25, 4])
    def test_replay_output_independent_of_speed(self, mock_sender, mock_input, replay_speed):
        """tests that output consistent and independent of replay speed
        """
        replay_log.replay(mock_input, replay_speed)
        assert mock_sender.getvalue() == mock_input.getvalue()

    @pytest.mark.parametrize("replay_speed", [0.25, 4])
    def test_replay_live_speed(self, mock_sender, mock_input, replay_speed):
        """tests that replay_log.replay sends data at given replay_speed
        """
        BENCHMARK_SPEED = 1
        benchmark_runtime = get_runtime(replay_log.replay, mock_input, BENCHMARK_SPEED)
        mock_input.seek(0)
        runtime = get_runtime(replay_log.replay, mock_input, replay_speed)
        # scale benchmark time by inverse of replay_speed
        # slower/smaller speed => longer expected_runtime
        expected_runtime = benchmark_runtime / replay_speed
        # 10% margin of error for varying computational resources/power
        percent_error = get_percent_error(runtime, expected_runtime)
        assert percent_error < 0.10
