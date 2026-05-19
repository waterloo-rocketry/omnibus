# pyright: standard

import queue
import socket
import threading
import time
from unittest.mock import Mock, patch

import pytest
import socketio

import server
from omnibus import Message as OmnibusMessage


@pytest.fixture(scope="session")
def server_url():
    """Start the SocketIO server on a free port in a daemon thread."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        port = sock.getsockname()[1]

    url = f"http://127.0.0.1:{port}"

    threading.Thread(
        target=lambda: server.socketio.run(
            server.app,
            host="127.0.0.1",
            port=port,
            log_output=False,
            allow_unsafe_werkzeug=True,
        ),
        daemon=True,
    ).start()

    probe = socketio.SimpleClient(serializer="msgpack")
    for _ in range(50):
        try:
            probe.connect(url)
            probe.disconnect()
            break
        except Exception:
            time.sleep(0.1)
    else:
        raise RuntimeError("Server did not start in time")

    yield url


@pytest.fixture(autouse=True)
def clean_state():
    server._workers_started = False
    server._zmq_outbound_queue = queue.Queue()
    server._ws_broadcast_queue = queue.Queue()
    yield
    server._workers_started = False
    server._zmq_outbound_queue = queue.Queue()
    server._ws_broadcast_queue = queue.Queue()


def make_client(url):
    client = socketio.SimpleClient(serializer="msgpack")
    client.connect(url)
    return client


class TestConnectAndDisconnect:
    def test_msgpack_exttype_auth_does_not_crash(self):
        mock_request = Mock()
        mock_request.sid = "browser-sid"

        class FakeExtType:
            pass

        with patch("server.request", new=mock_request):
            server.handle_connect(auth=FakeExtType())

    def test_disconnect_without_client_state_does_not_raise(self, server_url):
        client = make_client(server_url)
        client.disconnect()


class TestClientMessages:
    def test_client_message_queued_for_zmq_relay(self, server_url):
        client = make_client(server_url)
        try:
            client.emit("telemetry/altitude", (1234567890.0, {"alt": 1000}))
            client.receive(timeout=2)
            time.sleep(0.1)

            assert not server._zmq_outbound_queue.empty()
            sent = server._zmq_outbound_queue.get_nowait()
            assert sent.channel == "telemetry/altitude/WS_ORIGINATED"
            assert sent.timestamp == 1234567890.0
            assert sent.payload == {"alt": 1000}
        finally:
            client.disconnect()

    def test_client_message_broadcast_to_all(self, server_url):
        client1 = make_client(server_url)
        client2 = make_client(server_url)
        try:
            client1.emit("sensors/temp", (10.0, 42))

            event1, *data1 = client1.receive(timeout=2)
            event2, *data2 = client2.receive(timeout=2)

            assert event1 == "sensors/temp"
            assert event2 == "sensors/temp"
            assert data1 == [10.0, 42]
            assert data2 == [10.0, 42]
        finally:
            client2.disconnect()
            client1.disconnect()

    def test_client_message_works_without_other_clients(self, server_url):
        client = make_client(server_url)
        try:
            client.emit("telemetry", (1.0, {"v": 42}))

            event, *data = client.receive(timeout=2)
            assert event == "telemetry"
            assert data == [1.0, {"v": 42}]

            time.sleep(0.1)
            assert not server._zmq_outbound_queue.empty()
            sent = server._zmq_outbound_queue.get_nowait()
            assert sent.channel == "telemetry/WS_ORIGINATED"
        finally:
            client.disconnect()

    def test_no_zmq_relay_for_malformed_list_data(self, server_url):
        client = make_client(server_url)
        try:
            with patch("server.print") as mock_print:
                client.emit("ch", [1.0])
                time.sleep(0.5)
                assert server._zmq_outbound_queue.empty()
                mock_print.assert_any_call(
                    ">>> Malformed message on 'ch': expected 2 data args (timestamp, payload), got 1"
                )
        finally:
            client.disconnect()

    def test_no_zmq_relay_for_non_list_data(self, server_url):
        client = make_client(server_url)
        try:
            with patch("server.print") as mock_print:
                client.emit("ch", "not-a-list")
                time.sleep(0.5)
                assert server._zmq_outbound_queue.empty()
                mock_print.assert_any_call(
                    ">>> Malformed message on 'ch': expected 2 data args (timestamp, payload), got 1"
                )
        finally:
            client.disconnect()

    def test_broadcast_happens_before_zmq_enqueue(self):
        mock_request = Mock()
        mock_request.sid = "client-abc"

        call_order: list[str] = []
        original_put = server._zmq_outbound_queue.put

        with patch("server.request", new=mock_request), patch(
            "server.emit"
        ) as mock_emit, patch.object(
            server._zmq_outbound_queue,
            "put",
            side_effect=lambda msg: (
                call_order.append("zmq_enqueue"),
                original_put(msg),
            ),
        ):
            mock_emit.side_effect = lambda *args, **kwargs: call_order.append("sio")
            server.handle_channel_message("ch", 1.0, "data")

        assert call_order == ["sio", "zmq_enqueue"]


class _StopLoop(Exception):
    pass


class TestBackgroundWorkers:
    def test_sender_worker_forwards_to_zmq(self):
        mock_sender = Mock()
        msg = OmnibusMessage("test/WS_ORIGINATED", 1.0, {"v": 1})

        with patch.object(
            server._zmq_outbound_queue, "get", side_effect=[msg, _StopLoop]
        ):
            with pytest.raises(_StopLoop):
                server.send_messages_to_omnibus(
                    mock_sender, server._zmq_outbound_queue
                )

        mock_sender.send_message.assert_called_once_with(msg)

    def test_receiver_subscribes_to_all_channels(self):
        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = _StopLoop

        with patch("server.Receiver", return_value=mock_receiver) as mock_receiver_class:
            with pytest.raises(_StopLoop):
                server._run_zmq_receiver()

        mock_receiver_class.assert_called_once_with("")

    def test_receiver_uses_blocking_receive(self):
        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = _StopLoop

        with pytest.raises(_StopLoop):
            server.queue_messages_for_websocket(
                mock_receiver, server._ws_broadcast_queue
            )

        mock_receiver.recv_message.assert_called_once_with(None)

    def test_receiver_enqueues_non_ws_originated_message(self):
        mock_receiver = Mock()
        msg = OmnibusMessage("telemetry", 42.0, {"v": 1})

        with patch.object(
            mock_receiver, "recv_message", side_effect=[msg, _StopLoop]
        ):
            with pytest.raises(_StopLoop):
                server.queue_messages_for_websocket(
                    mock_receiver, server._ws_broadcast_queue
                )

        queued = server._ws_broadcast_queue.get_nowait()
        assert queued == msg

    def test_receiver_skips_ws_originated_message(self):
        mock_receiver = Mock()
        msg = OmnibusMessage("telemetry/WS_ORIGINATED", 42.0, {"v": 1})

        with patch.object(
            mock_receiver, "recv_message", side_effect=[msg, _StopLoop]
        ):
            with pytest.raises(_StopLoop):
                server.queue_messages_for_websocket(
                    mock_receiver, server._ws_broadcast_queue
                )

        assert server._ws_broadcast_queue.empty()

    def test_receiver_does_not_skip_similar_channel(self):
        mock_receiver = Mock()
        msg = OmnibusMessage("telemetry/WS_ORIGINATED/extra", 42.0, {"v": 1})

        with patch.object(
            mock_receiver, "recv_message", side_effect=[msg, _StopLoop]
        ):
            with pytest.raises(_StopLoop):
                server.queue_messages_for_websocket(
                    mock_receiver, server._ws_broadcast_queue
                )

        queued = server._ws_broadcast_queue.get_nowait()
        assert queued == msg

    def test_broadcast_worker_emits_message(self):
        msg = OmnibusMessage("telemetry", 10.0, {"v": 1})

        with patch.object(
            server._ws_broadcast_queue, "get", side_effect=[msg, _StopLoop]
        ), patch.object(server.socketio, "emit") as mock_emit:
            with pytest.raises(_StopLoop):
                server.broadcast_messages_to_websocket(server._ws_broadcast_queue)

        mock_emit.assert_called_once_with("telemetry", (10.0, {"v": 1}))

    def test_broadcast_queue_message_reaches_clients(self, server_url):
        client = make_client(server_url)
        msg = OmnibusMessage("telemetry/altitude", 1234567890.0, {"alt": 1000})

        try:
            with patch.object(
                server._ws_broadcast_queue, "get", side_effect=[msg, _StopLoop]
            ):
                with pytest.raises(_StopLoop):
                    server.broadcast_messages_to_websocket(
                        server._ws_broadcast_queue
                    )

            event, *data = client.receive(timeout=2)
            assert event == "telemetry/altitude"
            assert data == [1234567890.0, {"alt": 1000}]
        finally:
            client.disconnect()

    def test_start_background_workers_starts_each_thread_once(self):
        created_threads = []

        def thread_factory(*, name, target, daemon):
            thread = Mock()
            thread.name = name
            thread.target = target
            thread.daemon = daemon
            created_threads.append(thread)
            return thread

        with patch("server.threading.Thread", side_effect=thread_factory):
            server.start_background_workers()
            server.start_background_workers()

        assert [thread.name for thread in created_threads] == [
            "ws-zmq-sender",
            "ws-zmq-receiver",
            "ws-broadcast",
        ]

        for thread in created_threads:
            assert thread.daemon is True
            thread.start.assert_called_once_with()
