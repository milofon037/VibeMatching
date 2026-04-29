"""
Три стратегии кеширования для сравнения
"""
import time
from abc import ABC, abstractmethod
from typing import Any, Optional
import sqlite3
import json


class CacheMetrics:
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.db_reads = 0
        self.db_writes = 0
        self.read_times = []
        self.write_times = []
        self.total_requests = 0
    
    def hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0
    
    def avg_read_time(self) -> float:
        return sum(self.read_times) / len(self.read_times) if self.read_times else 0
    
    def avg_write_time(self) -> float:
        return sum(self.write_times) / len(self.write_times) if self.write_times else 0
    
    def __repr__(self):
        return (f"Metrics(hits={self.cache_hits}, misses={self.cache_misses}, "
                f"hit_rate={self.hit_rate():.2%}, db_reads={self.db_reads}, "
                f"db_writes={self.db_writes})")


class CacheStrategy(ABC):
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self.cache = {}
        self.metrics = CacheMetrics()
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE,
                value TEXT,
                updated_at TIMESTAMP
            )
        ''')
        cursor.execute('DELETE FROM data')
        self.conn.commit()
    
    def _db_read(self, key: str) -> Optional[str]:
        self.metrics.db_reads += 1
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM data WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def _db_write(self, key: str, value: str):
        self.metrics.db_writes += 1
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO data (key, value, updated_at) VALUES (?, ?, datetime("now"))',
            (key, value)
        )
        self.conn.commit()
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: str):
        pass


class LazyLoadingCacheStrategy(CacheStrategy):
    """
    Lazy Loading (Cache-Aside) стратегия:
    - Чтение через кеш
    - При промахе - чтение из БД и сохранение в кеш
    - Запись сразу в БД (без кеша)
    """
    
    def get(self, key: str) -> Optional[str]:
        start = time.time()
        
        # Проверяем кеш
        if key in self.cache:
            self.metrics.cache_hits += 1
            elapsed = time.time() - start
            self.metrics.read_times.append(elapsed)
            return self.cache[key]
        
        # Кеш пустой - читаем из БД
        self.metrics.cache_misses += 1
        value = self._db_read(key)
        
        # Сохраняем в кеш
        if value:
            self.cache[key] = value
        
        elapsed = time.time() - start
        self.metrics.read_times.append(elapsed)
        return value
    
    def set(self, key: str, value: str):
        start = time.time()
        # Запись идет только в БД
        self._db_write(key, value)
        elapsed = time.time() - start
        self.metrics.write_times.append(elapsed)


class WriteThroughCacheStrategy(CacheStrategy):
    """
    Write-Through стратегия:
    - Чтение через кеш
    - При записи - пишем одновременно в кеш и БД
    """
    
    def get(self, key: str) -> Optional[str]:
        start = time.time()
        
        # Проверяем кеш
        if key in self.cache:
            self.metrics.cache_hits += 1
            elapsed = time.time() - start
            self.metrics.read_times.append(elapsed)
            return self.cache[key]
        
        # Кеш пустой - читаем из БД
        self.metrics.cache_misses += 1
        value = self._db_read(key)
        
        # Сохраняем в кеш
        if value:
            self.cache[key] = value
        
        elapsed = time.time() - start
        self.metrics.read_times.append(elapsed)
        return value
    
    def set(self, key: str, value: str):
        start = time.time()
        # Запись в кеш и БД одновременно
        self.cache[key] = value
        self._db_write(key, value)
        elapsed = time.time() - start
        self.metrics.write_times.append(elapsed)


class WriteBackCacheStrategy(CacheStrategy):
    """
    Write-Back (Write-Behind) стратегия:
    - Чтение через кеш
    - При записи - пишем в кеш сразу
    - Запись в БД отложена (в конце или периодически)
    """
    
    def __init__(self, db_path: str = ":memory:"):
        super().__init__(db_path)
        self.dirty_keys = set()  # Ключи, которые нужно записать в БД
    
    def get(self, key: str) -> Optional[str]:
        start = time.time()
        
        # Проверяем кеш
        if key in self.cache:
            self.metrics.cache_hits += 1
            elapsed = time.time() - start
            self.metrics.read_times.append(elapsed)
            return self.cache[key]
        
        # Кеш пустой - читаем из БД
        self.metrics.cache_misses += 1
        value = self._db_read(key)
        
        # Сохраняем в кеш
        if value:
            self.cache[key] = value
        
        elapsed = time.time() - start
        self.metrics.read_times.append(elapsed)
        return value
    
    def set(self, key: str, value: str):
        start = time.time()
        # Запись только в кеш - быстро!
        self.cache[key] = value
        self.dirty_keys.add(key)
        elapsed = time.time() - start
        self.metrics.write_times.append(elapsed)
    
    def flush_to_db(self):
        """Записать все отложенные данные в БД"""
        for key in self.dirty_keys:
            if key in self.cache:
                value = self.cache[key]
                # Используем прямое обращение без учета в метриках
                cursor = self.conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO data (key, value, updated_at) VALUES (?, ?, datetime("now"))',
                    (key, value)
                )
                self.conn.commit()
        self.dirty_keys.clear()
