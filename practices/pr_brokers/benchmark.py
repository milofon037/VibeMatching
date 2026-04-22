#!/usr/bin/env python3
import argparse
import json
import random
import statistics
import string
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

import pika
import redis

ALPHABET = string.ascii_letters + string.digits


@dataclass
class RunResult:
    run_id: str
    broker: str
    message_size_bytes: int
    target_rps: int
    warmup_seconds: int
    duration_seconds: int
    sent: int
    processed: int
    producer_errors: int
    consumer_errors: int
    lost: int
    throughput_sent_msg_s: float
    throughput_processed_msg_s: float
    latency_avg_ms: float
    latency_p95_ms: float
    latency_max_ms: float
    backlog_end: int
    degraded: bool
    timestamp_utc: str


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.latencies_ms: list[float] = []
        self.processed = 0
        self.consumer_errors = 0

    def record(self, latency_ms: float) -> None:
        with self._lock:
            self.latencies_ms.append(latency_ms)
            self.processed += 1

    def record_error(self) -> None:
        with self._lock:
            self.consumer_errors += 1

    def snapshot(self) -> tuple[list[float], int, int]:
        with self._lock:
            return list(self.latencies_ms), self.processed, self.consumer_errors


class RabbitBenchmarkClient:
    def __init__(self, host: str, port: int, run_id: str) -> None:
        self.host = host
        self.port = port
        self.run_id = run_id
        self.queue = f"bench.rabbit.{run_id}"
        self.stop_event = threading.Event()
        self.consumer_thread: Optional[threading.Thread] = None

        params = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            heartbeat=60,
            blocked_connection_timeout=300,
        )
        self.producer_conn = pika.BlockingConnection(params)
        self.producer_channel = self.producer_conn.channel()
        self.producer_channel.queue_delete(queue=self.queue)
        self.producer_channel.queue_declare(queue=self.queue, durable=False)

    def publish(self, payload: bytes) -> bool:
        self.producer_channel.basic_publish(
            exchange="",
            routing_key=self.queue,
            body=payload,
            properties=pika.BasicProperties(
                delivery_mode=1,
                content_type="application/json",
            ),
            mandatory=True,
        )
        return True

    def start_consumer(self, metrics: Metrics, prefetch: int = 500) -> None:
        self.consumer_thread = threading.Thread(
            target=self._consume,
            args=(metrics, prefetch),
            daemon=True,
        )
        self.consumer_thread.start()

    def _consume(self, metrics: Metrics, prefetch: int) -> None:
        params = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            heartbeat=60,
            blocked_connection_timeout=300,
        )
        conn = pika.BlockingConnection(params)
        channel = conn.channel()
        channel.queue_declare(queue=self.queue, durable=False)
        channel.basic_qos(prefetch_count=prefetch)

        def on_message(ch, method, _properties, body: bytes) -> None:
            try:
                event = json.loads(body)
                if not event.get("warmup", False):
                    latency_ms = (time.time_ns() - int(event["sent_ns"])) / 1_000_000
                    metrics.record(latency_ms)
            except Exception:
                metrics.record_error()
            finally:
                ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(
            queue=self.queue,
            on_message_callback=on_message,
            auto_ack=False,
        )

        while not self.stop_event.is_set():
            # Drain callbacks in small time slices so thread can stop promptly.
            conn.process_data_events(time_limit=1)

        try:
            channel.cancel()
        except Exception:
            pass

        conn.close()

    def backlog(self) -> int:
        queue_info = self.producer_channel.queue_declare(queue=self.queue, passive=True)
        return int(queue_info.method.message_count)

    def close(self) -> None:
        self.stop_event.set()
        if self.consumer_thread:
            self.consumer_thread.join(timeout=10)
        try:
            self.producer_channel.queue_delete(queue=self.queue)
        except Exception:
            pass
        self.producer_conn.close()


class RedisBenchmarkClient:
    def __init__(self, host: str, port: int, run_id: str) -> None:
        self.host = host
        self.port = port
        self.run_id = run_id
        self.stream = f"bench.redis.stream.{run_id}"
        self.group = "bench-group"
        self.consumer = f"consumer-{uuid.uuid4().hex[:8]}"
        self.stop_event = threading.Event()
        self.consumer_thread: Optional[threading.Thread] = None

        self.client = redis.Redis(host=self.host, port=self.port, decode_responses=False)
        self.client.delete(self.stream)
        self.client.xgroup_create(name=self.stream, groupname=self.group, id="0", mkstream=True)

    def publish(self, payload: bytes) -> bool:
        self.client.xadd(self.stream, {"body": payload})
        return True

    def start_consumer(self, metrics: Metrics, read_count: int = 100) -> None:
        self.consumer_thread = threading.Thread(
            target=self._consume,
            args=(metrics, read_count),
            daemon=True,
        )
        self.consumer_thread.start()

    def _consume(self, metrics: Metrics, read_count: int) -> None:
        while not self.stop_event.is_set():
            try:
                data = self.client.xreadgroup(
                    groupname=self.group,
                    consumername=self.consumer,
                    streams={self.stream: ">"},
                    count=read_count,
                    block=1000,
                )
                if not data:
                    continue

                for _stream, entries in data:
                    for message_id, fields in entries:
                        try:
                            raw = fields[b"body"]
                            event = json.loads(raw)
                            if not event.get("warmup", False):
                                latency_ms = (time.time_ns() - int(event["sent_ns"])) / 1_000_000
                                metrics.record(latency_ms)
                        except Exception:
                            metrics.record_error()
                        finally:
                            self.client.xack(self.stream, self.group, message_id)
            except Exception:
                metrics.record_error()

    def backlog(self) -> int:
        pending_raw = self.client.xpending(self.stream, self.group)
        if isinstance(pending_raw, dict):
            pending = int(pending_raw.get("pending", 0))
        else:
            pending = int(pending_raw[0]) if pending_raw else 0

        lag = 0
        groups = self.client.xinfo_groups(self.stream)
        for group_info in groups:
            name = group_info.get(b"name", b"").decode()
            if name == self.group:
                lag_val = group_info.get(b"lag")
                if lag_val is not None:
                    lag = int(lag_val)
                break

        return max(0, pending + lag)

    def close(self) -> None:
        self.stop_event.set()
        if self.consumer_thread:
            self.consumer_thread.join(timeout=10)
        try:
            self.client.delete(self.stream)
        except Exception:
            pass
        self.client.close()


def build_payload(message_size: int, warmup: bool, rnd: random.Random) -> bytes:
    base = {
        "id": uuid.uuid4().hex,
        "sent_ns": time.time_ns(),
        "warmup": warmup,
        "payload": "",
    }
    base_raw = json.dumps(base, separators=(",", ":")).encode("utf-8")

    # Reserve 2 bytes for surrounding JSON string quotes in payload field.
    payload_len = max(0, message_size - len(base_raw) - 2)
    payload_data = "".join(rnd.choices(ALPHABET, k=payload_len))
    base["payload"] = payload_data

    return json.dumps(base, separators=(",", ":")).encode("utf-8")


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = min(len(sorted_vals) - 1, int(round((p / 100.0) * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


def run_benchmark(
    broker: str,
    host: str,
    port: int,
    message_size: int,
    target_rps: int,
    warmup_seconds: int,
    duration_seconds: int,
    drain_timeout_seconds: int,
    run_id: Optional[str] = None,
) -> RunResult:
    run_id = run_id or f"{broker}-{uuid.uuid4().hex[:10]}"
    metrics = Metrics()
    producer_errors = 0
    sent = 0

    client: RabbitBenchmarkClient | RedisBenchmarkClient
    if broker == "rabbitmq":
        client = RabbitBenchmarkClient(host=host, port=port, run_id=run_id)
    elif broker == "redis":
        client = RedisBenchmarkClient(host=host, port=port, run_id=run_id)
    else:
        raise ValueError(f"Unsupported broker: {broker}")

    client.start_consumer(metrics)

    rnd = random.Random(42)
    total_seconds = warmup_seconds + duration_seconds
    start = time.perf_counter()
    next_send = start
    interval = 1.0 / target_rps

    try:
        while (time.perf_counter() - start) < total_seconds:
            now = time.perf_counter()
            if now < next_send:
                time.sleep(next_send - now)
                continue

            warmup = (now - start) < warmup_seconds
            payload = build_payload(message_size=message_size, warmup=warmup, rnd=rnd)
            try:
                ok = client.publish(payload)
                if ok and not warmup:
                    sent += 1
                elif not ok:
                    producer_errors += 1
            except Exception:
                producer_errors += 1

            next_send += interval
            if (now - next_send) > 1.0:
                next_send = now

        wait_until = time.time() + drain_timeout_seconds
        while time.time() < wait_until:
            _latencies, processed, _consumer_errors = metrics.snapshot()
            if processed >= sent:
                break
            time.sleep(0.2)

        latencies, processed, consumer_errors = metrics.snapshot()
        backlog_end = client.backlog()
    finally:
        client.close()

    lost = max(0, sent - processed)
    throughput_sent = sent / duration_seconds if duration_seconds else 0.0
    throughput_processed = processed / duration_seconds if duration_seconds else 0.0
    latency_avg = statistics.fmean(latencies) if latencies else 0.0
    latency_p95 = percentile(latencies, 95)
    latency_max = max(latencies) if latencies else 0.0

    degraded = False
    if sent > 0:
        processed_ratio = processed / sent
        degraded = (
            processed_ratio < 0.95
            or latency_p95 > 500.0
            or backlog_end > int(0.1 * sent)
        )

    return RunResult(
        run_id=run_id,
        broker=broker,
        message_size_bytes=message_size,
        target_rps=target_rps,
        warmup_seconds=warmup_seconds,
        duration_seconds=duration_seconds,
        sent=sent,
        processed=processed,
        producer_errors=producer_errors,
        consumer_errors=consumer_errors,
        lost=lost,
        throughput_sent_msg_s=round(throughput_sent, 2),
        throughput_processed_msg_s=round(throughput_processed, 2),
        latency_avg_ms=round(latency_avg, 3),
        latency_p95_ms=round(latency_p95, 3),
        latency_max_ms=round(latency_max, 3),
        backlog_end=backlog_end,
        degraded=degraded,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RabbitMQ vs Redis single-node benchmark")
    parser.add_argument("--broker", choices=["rabbitmq", "redis"], required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--message-size", type=int, required=True)
    parser.add_argument("--target-rps", type=int, required=True)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--duration", type=int, default=30)
    parser.add_argument("--drain-timeout", type=int, default=20)
    parser.add_argument("--run-id", help="Optional run identifier for external orchestration")
    parser.add_argument("--output", help="Append NDJSON result to file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_benchmark(
        broker=args.broker,
        host=args.host,
        port=args.port,
        message_size=args.message_size,
        target_rps=args.target_rps,
        warmup_seconds=args.warmup,
        duration_seconds=args.duration,
        drain_timeout_seconds=args.drain_timeout,
        run_id=args.run_id,
    )

    result_json = json.dumps(asdict(result), ensure_ascii=True)
    print(result_json)

    if args.output:
        with open(args.output, "a", encoding="utf-8") as f:
            f.write(result_json + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
