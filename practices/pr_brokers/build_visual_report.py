#!/usr/bin/env python3
import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_int(row: dict, key: str) -> int:
    return int(float(row[key]))


def to_float(row: dict, key: str) -> float:
    return float(row[key])


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def aggregate_by_scenario(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        key = (row["broker"], to_int(row, "message_size_bytes"), to_int(row, "target_rps"))
        grouped[key].append(row)

    result = []
    for (broker, size, rps), group_rows in sorted(grouped.items(), key=lambda x: (x[0][1], x[0][2], x[0][0])):
        degraded_runs = sum(1 for r in group_rows if str(r["degraded"]).lower() == "true")
        runs = len(group_rows)
        stable_degraded = degraded_runs / runs >= 0.5 if runs >= 2 else degraded_runs == 1

        result.append(
            {
                "broker": broker,
                "message_size_bytes": size,
                "target_rps": rps,
                "runs": runs,
                "degraded_runs": degraded_runs,
                "stable_degraded": stable_degraded,
                "throughput_processed_msg_s": round(median([to_float(r, "throughput_processed_msg_s") for r in group_rows]), 3),
                "latency_p95_ms": round(median([to_float(r, "latency_p95_ms") for r in group_rows]), 3),
                "latency_avg_ms": round(median([to_float(r, "latency_avg_ms") for r in group_rows]), 3),
                "lost": int(median([to_int(r, "lost") for r in group_rows])),
                "backlog_end": int(median([to_int(r, "backlog_end") for r in group_rows])),
                "cpu_avg_perc": round(median([to_float(r, "cpu_avg_perc") for r in group_rows]), 3),
                "cpu_p95_perc": round(median([to_float(r, "cpu_p95_perc") for r in group_rows]), 3),
                "cpu_max_perc": round(median([to_float(r, "cpu_max_perc") for r in group_rows]), 3),
                "ram_avg_mb": round(median([to_float(r, "ram_avg_mb") for r in group_rows]), 3),
                "ram_max_mb": round(median([to_float(r, "ram_max_mb") for r in group_rows]), 3),
            }
        )
    return result


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def prepare_series(agg_rows: list[dict], size: int, broker: str, metric: str) -> tuple[list[int], list[float]]:
    filtered = [r for r in agg_rows if r["message_size_bytes"] == size and r["broker"] == broker]
    filtered.sort(key=lambda r: r["target_rps"])
    return [r["target_rps"] for r in filtered], [float(r[metric]) for r in filtered]


def plot_lines(agg_rows: list[dict], output_dir: Path, metric: str, ylabel: str, filename_prefix: str) -> list[str]:
    files = []
    sizes = sorted({r["message_size_bytes"] for r in agg_rows})
    for size in sizes:
        plt.figure(figsize=(10, 6))
        for broker in ["rabbitmq", "redis"]:
            x, y = prepare_series(agg_rows, size, broker, metric)
            if x:
                plt.plot(x, y, marker="o", label=broker)

        plt.title(f"{ylabel} vs Target RPS (payload={size}B)")
        plt.xlabel("Target RPS")
        plt.ylabel(ylabel)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        out_file = output_dir / f"{filename_prefix}_{size}B.png"
        plt.savefig(out_file, dpi=140)
        plt.close()
        files.append(out_file.name)
    return files


def build_markdown(output_dir: Path, chart_files: dict[str, list[str]]) -> None:
    md = []
    md.append("# Визуальный отчет")
    md.append("")
    md.append("## Содержимое")
    md.append("")
    md.append("- `summary_by_scenario.csv` — агрегированные метрики (медианы по повторам)")
    md.append("- `degradation_points.csv` — точки устойчивой деградации")
    md.append("- `charts/*.png` — графики сравнения по ключевым метрикам")
    md.append("")

    sections = [
        ("throughput", "Пропускная способность vs RPS"),
        ("p95", "p95 задержка vs RPS"),
        ("cpu", "CPU avg vs RPS"),
        ("ram", "RAM avg (MB) vs RPS"),
    ]

    for key, title in sections:
        md.append(f"## {title}")
        md.append("")
        for fname in chart_files.get(key, []):
            md.append(f"![{fname}](charts/{fname})")
            md.append("")

    (output_dir / "VISUAL_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Построить визуальный отчет по результатам бенчмарка")
    parser.add_argument("--results-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    results_csv = Path(args.results_csv)
    output_dir = Path(args.output_dir)
    charts_dir = output_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(results_csv)
    agg_rows = aggregate_by_scenario(rows)

    summary_file = output_dir / "summary_by_scenario.csv"
    summary_fields = [
        "broker",
        "message_size_bytes",
        "target_rps",
        "runs",
        "degraded_runs",
        "stable_degraded",
        "throughput_processed_msg_s",
        "latency_p95_ms",
        "latency_avg_ms",
        "lost",
        "backlog_end",
        "cpu_avg_perc",
        "cpu_p95_perc",
        "cpu_max_perc",
        "ram_avg_mb",
        "ram_max_mb",
    ]
    write_csv(summary_file, agg_rows, summary_fields)

    degr_rows = []
    for broker in ["rabbitmq", "redis"]:
        candidates = [r for r in agg_rows if r["broker"] == broker and r["stable_degraded"]]
        candidates.sort(key=lambda r: (r["target_rps"], r["message_size_bytes"]))
        if candidates:
            first = candidates[0]
            degr_rows.append(
                {
                    "broker": broker,
                    "message_size_bytes": first["message_size_bytes"],
                    "target_rps": first["target_rps"],
                    "latency_p95_ms": first["latency_p95_ms"],
                    "backlog_end": first["backlog_end"],
                    "runs": first["runs"],
                    "degraded_runs": first["degraded_runs"],
                }
            )
        else:
            degr_rows.append(
                {
                    "broker": broker,
                    "message_size_bytes": "-",
                    "target_rps": "-",
                    "latency_p95_ms": "-",
                    "backlog_end": "-",
                    "runs": "-",
                    "degraded_runs": "-",
                }
            )

    degr_file = output_dir / "degradation_points.csv"
    degr_fields = ["broker", "message_size_bytes", "target_rps", "latency_p95_ms", "backlog_end", "runs", "degraded_runs"]
    write_csv(degr_file, degr_rows, degr_fields)

    chart_files = {
        "throughput": plot_lines(agg_rows, charts_dir, "throughput_processed_msg_s", "Throughput (msg/s)", "throughput_vs_rps"),
        "p95": plot_lines(agg_rows, charts_dir, "latency_p95_ms", "Latency p95 (ms)", "latency_p95_vs_rps"),
        "cpu": plot_lines(agg_rows, charts_dir, "cpu_avg_perc", "CPU avg (%)", "cpu_avg_vs_rps"),
        "ram": plot_lines(agg_rows, charts_dir, "ram_avg_mb", "RAM avg (MB)", "ram_avg_vs_rps"),
    }
    build_markdown(output_dir, chart_files)

    print(f"Сохранено: {summary_file}")
    print(f"Сохранено: {degr_file}")
    print(f"Сохранено: {output_dir / 'VISUAL_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
