"""
Главный скрипт для запуска всех тестов и генерации отчета
"""
import os
import json
import tempfile
from datetime import datetime
from pathlib import Path
import socket
import time

# Load .env file FIRST before importing cache_strategies
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from cache_strategies import LazyLoadingCacheStrategy, WriteThroughCacheStrategy, WriteBackCacheStrategy
from load_generator import run_test


def wait_for_tcp(host: str, port: int, timeout: int = 30):
    """Ожидание появления доступного TCP сервиса"""
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except Exception:
            if time.time() - start > timeout:
                raise
            time.sleep(0.5)


def save_raw_results(results, filename='test_metrics.json'):
    """Сохраняет сырые результаты тестов в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✓ Метрики сохранены в: {filename}")
    return filename


def load_test_results(filename='test_metrics.json'):
    """Загружает результаты тестов из JSON файла"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_report_from_metrics(metrics_file='test_metrics.json', report_file='report.md'):
    """Генерирует отчет на основе реальных метрик"""
    
    # Загружаем результаты
    results = load_test_results(metrics_file)
    
    # Начало отчета
    report = f"""# Отчет: Сравнение типов кеширования

**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Источник метрик:** {metrics_file}

## Сводка

Проведено тестирование трех основных стратегий кеширования:
- **Lazy Loading (Cache-Aside)** - кеш используется для чтения, запись идет только в БД
- **Write-Through** - запись идет одновременно в кеш и БД
- **Write-Back (Write-Behind)** - запись в кеш моментальна, в БД отложена

## Результаты тестирования

"""
    
    # Таблица для каждой конфигурации
    for config in results:
        config_name = config['config']
        report += f"\n### {config_name}\n\n"
        
        # Создаем таблицу результатов
        report += "| Метрика | Lazy Loading | Write-Through | Write-Back |\n"
        report += "|---------|--------------|---------------|------------|\n"
        
        # Извлекаем данные из результатов
        strategies = config['strategies']
        
        metrics_names = [
            ('throughput', 'Пропускная способность'),
            ('elapsed_time', 'Время выполнения'),
            ('avg_read_time', 'Среднее время чтения'),
            ('avg_write_time', 'Среднее время записи'),
            ('hit_rate', 'Hit Rate кеша'),
            ('db_reads', 'Обращений в БД (чтение)'),
            ('db_writes', 'Обращений в БД (запись)'),
        ]
        
        for metric_key, metric_name in metrics_names:
            row = f"| {metric_name} |"
            for strategy in strategies:
                value = strategy.get(metric_key, 'N/A')
                row += f" {value} |"
            report += row + "\n"
    
    # Сохраняем отчет
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ Отчет сохранен в: {report_file}")
    return report


def run_all_tests():
    """Запускает все тесты и собирает результаты"""
    
    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ СТРАТЕГИЙ КЕШИРОВАНИЯ")
    print("="*70)
    
    test_configs = [
        ("Read-Heavy (80% read / 20% write)", 0.8),
        ("Balanced (50% read / 50% write)", 0.5),
        ("Write-Heavy (20% read / 80% write)", 0.2),
    ]
    
    all_results = []
    
    for config_name, read_ratio in test_configs:
        print(f"\n\n{'#'*70}")
        print(f"КОНФИГУРАЦИЯ: {config_name}")
        print(f"{'#'*70}")
        
        config_results = {
            'config': config_name,
            'strategies': []
        }
        
        # Lazy Loading
        cache = LazyLoadingCacheStrategy()
        cache.clear_all()  # Очищаем перед тестом
        result = run_test("Lazy Loading (Cache-Aside)", cache, read_ratio, num_operations=1000, num_keys=50)
        config_results['strategies'].append(result)

        # Write-Through
        cache = WriteThroughCacheStrategy()
        cache.clear_all()  # Очищаем перед тестом
        result = run_test("Write-Through", cache, read_ratio, num_operations=1000, num_keys=50)
        config_results['strategies'].append(result)

        # Write-Back
        cache = WriteBackCacheStrategy()
        cache.clear_all()  # Очищаем перед тестом
        result = run_test("Write-Back (Write-Behind)", cache, read_ratio, num_operations=1000, num_keys=50)
        config_results['strategies'].append(result)
        
        all_results.append(config_results)
    
    return all_results


def main():
    """Главная функция"""
    print("\n" + "="*70)
    print("ЭТАП 0: ОЖИДАНИЕ СЕРВИСОВ (Redis, Postgres)")
    print("="*70)

    pg_host = os.getenv('POSTGRES_HOST', 'localhost')
    pg_port = int(os.getenv('POSTGRES_PORT', 5433))
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6380))

    print(f"Подключение к: Postgres {pg_host}:{pg_port}, Redis {redis_host}:{redis_port}")
    
    try:
        wait_for_tcp(pg_host, pg_port, timeout=30)
        print(f"✓ Postgres доступен на {pg_host}:{pg_port}")
        wait_for_tcp(redis_host, redis_port, timeout=30)
        print(f"✓ Redis доступен на {redis_host}:{redis_port}")
    except Exception as e:
        print(f'❌ Ошибка подключения: {e}')
        print('Убедитесь что контейнеры запущены: docker compose ps')
        return

    print("\n" + "="*70)
    print("ЭТАП 1: ЗАПУСК ТЕСТОВ")
    print("="*70)

    # Запускаем все тесты
    results = run_all_tests()
    
    print("\n" + "="*70)
    print("ЭТАП 2: СОХРАНЕНИЕ МЕТРИК")
    print("="*70)
    
    # Сохраняем сырые результаты в JSON
    save_raw_results(results, 'test_metrics.json')
    
    print("\n" + "="*70)
    print("ЭТАП 3: ГЕНЕРАЦИЯ ОТЧЕТА")
    print("="*70)
    
    # Генерируем отчет на основе сохраненных метрик
    generate_report_from_metrics('test_metrics.json', 'report.md')
    
    print("\n" + "="*70)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*70)
    print("\nФайлы:")
    print("  - test_metrics.json (сырые метрики)")
    print("  - report.md (итоговый отчет)")


if __name__ == "__main__":
    main()
