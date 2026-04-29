"""
Главный скрипт для запуска всех тестов и генерации отчета
"""
import os
import json
import tempfile
from datetime import datetime
from cache_strategies import LazyLoadingCacheStrategy, WriteThroughCacheStrategy, WriteBackCacheStrategy
from load_generator import run_test


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
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        cache = LazyLoadingCacheStrategy(db_path=db_path)
        result = run_test("Lazy Loading (Cache-Aside)", cache, read_ratio, num_operations=1000, num_keys=50)
        config_results['strategies'].append(result)
        os.unlink(db_path)
        
        # Write-Through
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        cache = WriteThroughCacheStrategy(db_path=db_path)
        result = run_test("Write-Through", cache, read_ratio, num_operations=1000, num_keys=50)
        config_results['strategies'].append(result)
        os.unlink(db_path)
        
        # Write-Back
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        cache = WriteBackCacheStrategy(db_path=db_path)
        result = run_test("Write-Back (Write-Behind)", cache, read_ratio, num_operations=1000, num_keys=50)
        config_results['strategies'].append(result)
        os.unlink(db_path)
        
        all_results.append(config_results)
    
    return all_results


def main():
    """Главная функция"""
    
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
