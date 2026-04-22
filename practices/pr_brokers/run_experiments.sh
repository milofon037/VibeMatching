#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -x "${ROOT_DIR}/../../../.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/../../../.venv/bin/python"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

"$PYTHON_BIN" -m pip install -r requirements.txt

docker compose up -d rabbitmq redis

echo "Ожидание готовности брокеров..."
sleep 12

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${ROOT_DIR}/results/${STAMP}"
mkdir -p "$OUT_DIR"
RAW_FILE="${OUT_DIR}/raw.ndjson"
RESOURCE_FILE="${OUT_DIR}/resource_stats.csv"

echo "timestamp_utc,run_id,broker,cpu_perc,mem_used,mem_limit,mem_perc" > "$RESOURCE_FILE"

message_sizes=(128 1024 10240 102400)
load_rps=(1000 5000 10000)

# Tune behavior via env vars when needed.
BENCH_REPEATS="${BENCH_REPEATS:-3}"
BENCH_COOLDOWN_SECONDS="${BENCH_COOLDOWN_SECONDS:-5}"
BENCH_SAMPLE_INTERVAL_SECONDS="${BENCH_SAMPLE_INTERVAL_SECONDS:-1}"

# Denser stress ladders improve degradation point detection.
stress_rps=(12000 14000 16000 18000 20000 25000 30000 35000 40000 45000 50000)
heavy_stress_rps=(1000 1500 2000 2500 3000 4000 5000)

monitor_resource_usage() {
  local container="$1"
  local broker="$2"
  local run_id="$3"
  local output_file="$4"
  local stop_file="$5"
  local interval_seconds="$6"

  while [[ ! -f "$stop_file" ]]; do
    local ts
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    local line
    line="$(docker stats --no-stream --format '{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}' "$container" 2>/dev/null || true)"

    if [[ -n "$line" ]]; then
      local cpu
      local rest
      local mem_usage
      local mem_perc
      local mem_used
      local mem_limit

      cpu="${line%%|*}"
      rest="${line#*|}"
      mem_usage="${rest%%|*}"
      mem_perc="${rest##*|}"
      mem_used="${mem_usage%% / *}"
      mem_limit="${mem_usage##* / }"

      echo "${ts},${run_id},${broker},${cpu},${mem_used},${mem_limit},${mem_perc}" >> "$output_file"
    fi

    sleep "$interval_seconds"
  done
}

run_case() {
  local broker="$1"
  local size="$2"
  local rps="$3"
  local duration="$4"
  local warmup="$5"
  local repeat_idx="$6"

  local host
  local port
  local container

  case "$broker" in
    rabbitmq)
      host="127.0.0.1"
      port="5672"
      container="pr-brokers-rabbitmq"
      ;;
    redis)
      host="127.0.0.1"
      port="6379"
      container="pr-brokers-redis"
      ;;
    *)
      echo "Неизвестный брокер: $broker" >&2
      exit 1
      ;;
  esac

  local run_id
  run_id="${broker}-r${repeat_idx}-s${size}-q${rps}-${RANDOM}${RANDOM}"

  local stop_file
  stop_file="${OUT_DIR}/.stop_${run_id}"
  rm -f "$stop_file"

  monitor_resource_usage "$container" "$broker" "$run_id" "$RESOURCE_FILE" "$stop_file" "$BENCH_SAMPLE_INTERVAL_SECONDS" &
  local monitor_pid=$!

  echo "Запуск: repeat=${repeat_idx} broker=${broker} size=${size} rps=${rps} run_id=${run_id}"
  "$PYTHON_BIN" benchmark.py \
    --broker "$broker" \
    --host "$host" \
    --port "$port" \
    --message-size "$size" \
    --target-rps "$rps" \
    --warmup "$warmup" \
    --duration "$duration" \
    --drain-timeout 20 \
    --run-id "$run_id" \
    --output "$RAW_FILE"

  touch "$stop_file"
  wait "$monitor_pid" || true
  rm -f "$stop_file"

  if [[ "$BENCH_COOLDOWN_SECONDS" -gt 0 ]]; then
    sleep "$BENCH_COOLDOWN_SECONDS"
  fi
}

for repeat_idx in $(seq 1 "$BENCH_REPEATS"); do
  echo "=== Повтор ${repeat_idx}/${BENCH_REPEATS} ==="

  cases=()

  # 1) Base matrix from the task.
  for size in "${message_sizes[@]}"; do
    for rps in "${load_rps[@]}"; do
      cases+=("rabbitmq|${size}|${rps}|30|10")
      cases+=("redis|${size}|${rps}|30|10")
    done
  done

  # 2) Stress progression for 1KB payload.
  for rps in "${stress_rps[@]}"; do
    cases+=("rabbitmq|1024|${rps}|20|5")
    cases+=("redis|1024|${rps}|20|5")
  done

  # 3) Heavy payload stress.
  for rps in "${heavy_stress_rps[@]}"; do
    cases+=("rabbitmq|102400|${rps}|20|5")
    cases+=("redis|102400|${rps}|20|5")
  done

  if command -v shuf >/dev/null 2>&1; then
    mapfile -t shuffled_cases < <(printf '%s\n' "${cases[@]}" | shuf)
  else
    mapfile -t shuffled_cases < <(printf '%s\n' "${cases[@]}")
  fi

  for case_line in "${shuffled_cases[@]}"; do
    IFS='|' read -r broker size rps duration warmup <<< "$case_line"
    run_case "$broker" "$size" "$rps" "$duration" "$warmup" "$repeat_idx"
  done
done

"$PYTHON_BIN" aggregate_results.py --input "$RAW_FILE" --output-dir "$OUT_DIR"

echo "Результаты сохранены в: $OUT_DIR"

echo "Проверьте файлы report.md и results.csv"
