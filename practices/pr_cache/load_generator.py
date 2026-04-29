"""
Генератор нагрузки для тестирования стратегий кеширования
"""
import random
import time
from typing import Tuple, List
from cache_strategies import CacheStrategy


class LoadGenerator:
    """Генератор нагрузки для тестирования"""
    
    def __init__(self, cache_strategy: CacheStrategy):
        self.cache = cache_strategy
        self.operations = []
    
    def generate_workload(self, read_ratio: float, num_operations: int, num_keys: int) -> List[Tuple[str, str]]:
        """
        Генерирует рабочую нагрузку
        
        Args:
            read_ratio: доля операций чтения (0.0 - 1.0)
            num_operations: количество операций
            num_keys: количество ключей для работы
        
        Returns:
            Список операций [(операция, ключ), ...]
        """
        operations = []
        keys = [f"key_{i}" for i in range(num_keys)]
        
        for _ in range(num_operations):
            if random.random() < read_ratio:
                # Read операция
                key = random.choice(keys)
                operations.append(("read", key))
            else:
                # Write операция
                key = random.choice(keys)
                value = f"value_{random.randint(0, 10000)}"
                operations.append(("write", key, value))
        
        return operations
    
    def run_workload(self, workload: List[Tuple]) -> float:
        """
        Выполняет рабочую нагрузку и возвращает время выполнения
        """
        start_time = time.time()
        
        for operation in workload:
            if operation[0] == "read":
                self.cache.get(operation[1])
            else:  # write
                self.cache.set(operation[1], operation[2])
        
        elapsed = time.time() - start_time
        self.cache.metrics.total_requests = len(workload)
        return elapsed


def run_test(strategy_name: str, cache_strategy: CacheStrategy, read_ratio: float, 
             num_operations: int = 1000, num_keys: int = 50) -> dict:
    """
    Запускает одну конфигурацию теста
    """
    print(f"\n{'='*60}")
    print(f"Тест: {strategy_name}")
    print(f"Read Ratio: {read_ratio:.0%}, Operations: {num_operations}, Keys: {num_keys}")
    print(f"{'='*60}")
    
    generator = LoadGenerator(cache_strategy)
    workload = generator.generate_workload(read_ratio, num_operations, num_keys)
    
    # Запускаем тест
    elapsed_time = generator.run_workload(workload)
    
    # Если это Write-Back стратегия, нужно записать данные в БД
    if hasattr(cache_strategy, 'flush_to_db'):
        cache_strategy.flush_to_db()
    
    # Вычисляем метрики
    throughput = num_operations / elapsed_time if elapsed_time > 0 else 0
    metrics = cache_strategy.metrics
    
    results = {
        'strategy': strategy_name,
        'read_ratio': f"{read_ratio:.0%}",
        'operations': num_operations,
        'elapsed_time': f"{elapsed_time:.3f}s",
        'throughput': f"{throughput:.2f} req/sec",
        'avg_read_time': f"{metrics.avg_read_time()*1000:.2f}ms",
        'avg_write_time': f"{metrics.avg_write_time()*1000:.2f}ms",
        'cache_hits': metrics.cache_hits,
        'cache_misses': metrics.cache_misses,
        'hit_rate': f"{metrics.hit_rate():.2%}",
        'db_reads': metrics.db_reads,
        'db_writes': metrics.db_writes,
    }
    
    # Выводим результаты
    print(f"\nРезультаты:")
    print(f"  Пропускная способность: {results['throughput']}")
    print(f"  Время выполнения: {results['elapsed_time']}")
    print(f"  Среднее время чтения: {results['avg_read_time']}")
    print(f"  Среднее время записи: {results['avg_write_time']}")
    print(f"  Hit Rate кеша: {results['hit_rate']}")
    print(f"  Обращений в БД (read/write): {results['db_reads']}/{results['db_writes']}")
    
    return results
