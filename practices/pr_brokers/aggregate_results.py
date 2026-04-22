#!/usr/bin/env python3
import argparse
import csv
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path


def load_results(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def parse_percent(value: str) -> float:
    cleaned = (value or "").strip().replace("%", "")
    if not cleaned:
        return 0.0
    return float(cleaned)


def parse_size_to_mb(value: str) -> float:
    cleaned = (value or "").strip()
    match = re.match(r"^([0-9]*\.?[0-9]+)\s*([KMGTP]i?B|B)$", cleaned, re.IGNORECASE)
    if not match:
        return 0.0

    number = float(match.group(1))
    unit = match.group(2).lower()

    multipliers = {
        "b": 1 / (1024 * 1024),
        "kib": 1 / 1024,
        "kb": 1 / 1000,
        "mib": 1,
        "mb": 1,
        "gib": 1024,
        "gb": 1000,
        "tib": 1024 * 1024,
        "tb": 1000 * 1000,
        "pib": 1024 * 1024 * 1024,
        "pb": 1000 * 1000 * 1000,
    }
    return number * multipliers.get(unit, 0.0)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = min(len(sorted_vals) - 1, int(round((p / 100.0) * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


def load_resource_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_resource_by_run(resource_rows: list[dict]) -> dict[str, dict]:
    by_run: dict[str, dict] = {}
    grouped = defaultdict(list)
    for row in resource_rows:
        grouped[row.get("run_id", "")].append(row)

    for run_id, rows in grouped.items():
        if not run_id:
            continue

        cpu_values = [parse_percent(r.get("cpu_perc", "0")) for r in rows]
        mem_used_values = [parse_size_to_mb(r.get("mem_used", "0MiB")) for r in rows]
        mem_perc_values = [parse_percent(r.get("mem_perc", "0")) for r in rows]

        by_run[run_id] = {
            "cpu_avg_perc": round(statistics.fmean(cpu_values), 3) if cpu_values else 0.0,
            "cpu_p95_perc": round(percentile(cpu_values, 95), 3),
            "cpu_max_perc": round(max(cpu_values), 3) if cpu_values else 0.0,
            "ram_avg_mb": round(statistics.fmean(mem_used_values), 3) if mem_used_values else 0.0,
            "ram_max_mb": round(max(mem_used_values), 3) if mem_used_values else 0.0,
            "ram_avg_perc": round(statistics.fmean(mem_perc_values), 3) if mem_perc_values else 0.0,
            "ram_max_perc": round(max(mem_perc_values), 3) if mem_perc_values else 0.0,
        }

    return by_run


def enrich_rows_with_resources(rows: list[dict], resource_by_run: dict[str, dict]) -> list[dict]:
    enriched = []
    for row in rows:
        run_id = row.get("run_id", "")
        resource = resource_by_run.get(
            run_id,
            {
                "cpu_avg_perc": 0.0,
                "cpu_p95_perc": 0.0,
                "cpu_max_perc": 0.0,
                "ram_avg_mb": 0.0,
                "ram_max_mb": 0.0,
                "ram_avg_perc": 0.0,
                "ram_max_perc": 0.0,
            },
        )
        enriched.append({**row, **resource})

    return enriched


def write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return

    fieldnames = [
        "run_id",
        "broker",
        "message_size_bytes",
        "target_rps",
        "warmup_seconds",
        "duration_seconds",
        "sent",
        "processed",
        "producer_errors",
        "consumer_errors",
        "lost",
        "throughput_sent_msg_s",
        "throughput_processed_msg_s",
        "latency_avg_ms",
        "latency_p95_ms",
        "latency_max_ms",
        "backlog_end",
        "degraded",
        "cpu_avg_perc",
        "cpu_p95_perc",
        "cpu_max_perc",
        "ram_avg_mb",
        "ram_max_mb",
        "ram_avg_perc",
        "ram_max_perc",
        "timestamp_utc",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pick_winner(rabbit: float, redis: float, higher_is_better: bool) -> str:
    if rabbit == redis:
        return "ничья"

    if higher_is_better:
        return "rabbitmq" if rabbit > redis else "redis"

    return "rabbitmq" if rabbit < redis else "redis"


def build_group_summary(rows: list[dict]) -> dict[tuple[str, int, int], dict]:
    grouped = defaultdict(list)
    for row in rows:
        key = (row["broker"], int(row["message_size_bytes"]), int(row["target_rps"]))
        grouped[key].append(row)

    summary: dict[tuple[str, int, int], dict] = {}
    for key, group_rows in grouped.items():
        degraded_runs = sum(1 for r in group_rows if bool(r.get("degraded", False)) is True)
        runs = len(group_rows)
        degraded_ratio = degraded_runs / runs if runs else 0.0

        stable_degraded = False
        if runs >= 2:
            stable_degraded = degraded_ratio >= 0.5
        elif runs == 1:
            stable_degraded = degraded_runs == 1

        summary[key] = {
            "runs": runs,
            "degraded_runs": degraded_runs,
            "degraded_ratio": degraded_ratio,
            "stable_degraded": stable_degraded,
            "throughput_processed_msg_s": statistics.median(float(r["throughput_processed_msg_s"]) for r in group_rows),
            "latency_p95_ms": statistics.median(float(r["latency_p95_ms"]) for r in group_rows),
            "lost": statistics.median(int(r["lost"]) for r in group_rows),
            "backlog_end": statistics.median(int(r["backlog_end"]) for r in group_rows),
            "cpu_avg_perc": statistics.median(float(r["cpu_avg_perc"]) for r in group_rows),
            "cpu_p95_perc": statistics.median(float(r["cpu_p95_perc"]) for r in group_rows),
            "cpu_max_perc": statistics.median(float(r["cpu_max_perc"]) for r in group_rows),
            "ram_avg_mb": statistics.median(float(r["ram_avg_mb"]) for r in group_rows),
            "ram_max_mb": statistics.median(float(r["ram_max_mb"]) for r in group_rows),
        }

    return summary


def build_summary(rows: list[dict], resource_rows_exist: bool) -> str:
    grouped = build_group_summary(rows)

    by_size = defaultdict(dict)
    for (broker, message_size, target_rps), values in grouped.items():
        if target_rps == 5000:
            by_size[message_size][broker] = values

    lines = []
    lines.append("# Отчет по бенчмарку")
    lines.append("")
    lines.append("## Финальная сравнительная таблица (target rps = 5000, медианы по повторам)")
    lines.append("")
    lines.append("| Размер сообщения | Метрика | RabbitMQ | Redis | Победитель |")
    lines.append("|---|---|---:|---:|---|")

    for size in sorted(by_size):
        pair = by_size[size]
        rabbit = pair.get("rabbitmq")
        redis_row = pair.get("redis")
        if not rabbit or not redis_row:
            continue

        rabbit_tp = float(rabbit["throughput_processed_msg_s"])
        redis_tp = float(redis_row["throughput_processed_msg_s"])
        tp_winner = pick_winner(rabbit_tp, redis_tp, higher_is_better=True)

        rabbit_p95 = float(rabbit["latency_p95_ms"])
        redis_p95 = float(redis_row["latency_p95_ms"])
        p95_winner = pick_winner(rabbit_p95, redis_p95, higher_is_better=False)

        rabbit_lost = int(rabbit["lost"])
        redis_lost = int(redis_row["lost"])
        lost_winner = pick_winner(rabbit_lost, redis_lost, higher_is_better=False)

        lines.append(f"| {size} B | Пропускная способность (msg/s) | {rabbit_tp:.2f} | {redis_tp:.2f} | {tp_winner} |")
        lines.append(f"| {size} B | p95 задержка (ms) | {rabbit_p95:.3f} | {redis_p95:.3f} | {p95_winner} |")
        lines.append(f"| {size} B | Потерянные сообщения | {rabbit_lost} | {redis_lost} | {lost_winner} |")

    lines.append("")
    lines.append("## Точка деградации (устойчивая: >=50% повторов)")
    lines.append("")
    lines.append("| Брокер | Размер сообщения | Target RPS | p95 (ms) | Финальный backlog | Повторы | Деградировавшие повторы |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for broker in ["rabbitmq", "redis"]:
        broker_candidates = []
        for (item_broker, size, rps), values in grouped.items():
            if item_broker != broker:
                continue
            if values["stable_degraded"]:
                broker_candidates.append((rps, size, values))

        broker_candidates.sort(key=lambda item: (item[0], item[1]))
        degraded = broker_candidates[0] if broker_candidates else None

        if degraded:
            rps, size, values = degraded
            lines.append(
                "| "
                f"{broker} | {size} | {rps} | "
                f"{float(values['latency_p95_ms']):.3f} | {int(values['backlog_end'])} | "
                f"{int(values['runs'])} | {int(values['degraded_runs'])} |"
            )
        else:
            lines.append(f"| {broker} | - | - | - | - | - | - |")

    if resource_rows_exist:
        lines.append("")
        lines.append("## Ресурсные метрики (target rps = 5000, медианы по повторам)")
        lines.append("")
        lines.append("| Размер сообщения | Брокер | CPU avg (%) | CPU p95 (%) | CPU max (%) | RAM avg (MB) | RAM max (MB) |")
        lines.append("|---:|---|---:|---:|---:|---:|---:|")

        for size in sorted(by_size):
            pair = by_size[size]
            for broker in ["rabbitmq", "redis"]:
                row = pair.get(broker)
                if not row:
                    continue
                lines.append(
                    f"| {size} | {broker} | {float(row['cpu_avg_perc']):.3f} | {float(row['cpu_p95_perc']):.3f} | "
                    f"{float(row['cpu_max_perc']):.3f} | {float(row['ram_avg_mb']):.3f} | {float(row['ram_max_mb']):.3f} |"
                )

    lines.append("")
    lines.append("## Примечания")
    lines.append("")
    lines.append("- В итоговых таблицах используются медианы по повторам каждого сценария.")
    lines.append("- Устойчивой деградацией считается состояние, которое наблюдается минимум в 50% повторов сценария.")
    if resource_rows_exist:
        lines.append("- CPU/RAM сняты автоматически из `docker stats` и агрегированы по run_id.")
    else:
        lines.append("- Файл `resource_stats.csv` не найден, ресурсные метрики не включены.")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Агрегировать NDJSON-результаты бенчмарка")
    parser.add_argument("--input", required=True, help="Входной NDJSON-файл")
    parser.add_argument("--output-dir", required=True, help="Папка для файлов отчета")
    parser.add_argument("--resource-input", help="CSV-файл с ресурсными метриками (опционально)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_results(input_path)
    resource_input = Path(args.resource_input) if args.resource_input else input_path.with_name("resource_stats.csv")
    resource_rows = load_resource_rows(resource_input)
    resource_by_run = build_resource_by_run(resource_rows)
    rows = enrich_rows_with_resources(rows, resource_by_run)

    csv_path = out_dir / "results.csv"
    md_path = out_dir / "report.md"

    write_csv(rows, csv_path)
    md_path.write_text(build_summary(rows, resource_rows_exist=bool(resource_rows)), encoding="utf-8")

    print(f"Сохранено: {csv_path}")
    print(f"Сохранено: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
