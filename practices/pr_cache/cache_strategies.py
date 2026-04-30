import os
import time
from abc import ABC, abstractmethod
from typing import Optional


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


class CacheStrategy(ABC):
    def __init__(self):
        try:
            import psycopg2
            import redis
        except ImportError as e:
            raise ImportError("psycopg2-binary and redis are required. Install with: pip install -r requirements.txt") from e

        self.psycopg2 = psycopg2
        self.redis_lib = redis

        # Postgres connection parameters
        self.pg_host = os.getenv('POSTGRES_HOST', 'localhost')
        self.pg_port = int(os.getenv('POSTGRES_PORT', 5433))
        self.pg_db = os.getenv('POSTGRES_DB', 'vibedb')
        self.pg_user = os.getenv('POSTGRES_USER', 'vibe')
        self.pg_password = os.getenv('POSTGRES_PASSWORD', 'vibepass')

        # Redis connection parameters
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6380))

        self.metrics = CacheMetrics()

        self._init_pg()
        self._init_redis()

    def _init_pg(self):
        dsn = (
            f"host={self.pg_host} port={self.pg_port} dbname={self.pg_db} "
            f"user={self.pg_user} password={self.pg_password}"
        )
        self.pg_conn = self.psycopg2.connect(dsn)
        self.pg_conn.autocommit = True
        cur = self.pg_conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS data (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE,
                value TEXT,
                updated_at TIMESTAMP DEFAULT now()
            )
            """
        )
        cur.close()

    def _init_redis(self):
        self.redis = self.redis_lib.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)

    def _db_read(self, key: str) -> Optional[str]:
        self.metrics.db_reads += 1
        cur = self.pg_conn.cursor()
        cur.execute('SELECT value FROM data WHERE key = %s', (key,))
        row = cur.fetchone()
        cur.close()
        return row[0] if row else None

    def _db_write(self, key: str, value: str):
        self.metrics.db_writes += 1
        cur = self.pg_conn.cursor()
        cur.execute(
            'INSERT INTO data (key, value, updated_at) VALUES (%s, %s, now()) '
            'ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at',
            (key, value),
        )
        cur.close()

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, key: str, value: str):
        pass


class LazyLoadingCacheStrategy(CacheStrategy):
    """Cache-Aside: read from cache, on miss read from DB and set cache; writes go to DB."""

    def get(self, key: str) -> Optional[str]:
        start = time.time()
        val = self.redis.get(key)
        if val is not None:
            self.metrics.cache_hits += 1
            self.metrics.read_times.append(time.time() - start)
            return val

        self.metrics.cache_misses += 1
        val = self._db_read(key)
        if val is not None:
            self.redis.set(key, val)
        self.metrics.read_times.append(time.time() - start)
        return val

    def set(self, key: str, value: str):
        start = time.time()
        self._db_write(key, value)
        self.metrics.write_times.append(time.time() - start)


class WriteThroughCacheStrategy(CacheStrategy):
    """Write-through: write to both cache and DB synchronously."""

    def get(self, key: str) -> Optional[str]:
        start = time.time()
        val = self.redis.get(key)
        if val is not None:
            self.metrics.cache_hits += 1
            self.metrics.read_times.append(time.time() - start)
            return val

        self.metrics.cache_misses += 1
        val = self._db_read(key)
        if val is not None:
            self.redis.set(key, val)
        self.metrics.read_times.append(time.time() - start)
        return val

    def set(self, key: str, value: str):
        start = time.time()
        self.redis.set(key, value)
        self._db_write(key, value)
        self.metrics.write_times.append(time.time() - start)


class WriteBackCacheStrategy(CacheStrategy):
    """Write-back: write to cache, flush to DB later."""

    def __init__(self):
        super().__init__()
        self.dirty_keys = set()

    def get(self, key: str) -> Optional[str]:
        start = time.time()
        val = self.redis.get(key)
        if val is not None:
            self.metrics.cache_hits += 1
            self.metrics.read_times.append(time.time() - start)
            return val

        self.metrics.cache_misses += 1
        val = self._db_read(key)
        if val is not None:
            self.redis.set(key, val)
        self.metrics.read_times.append(time.time() - start)
        return val

    def set(self, key: str, value: str):
        start = time.time()
        self.redis.set(key, value)
        self.dirty_keys.add(key)
        self.metrics.write_times.append(time.time() - start)

    def flush_to_db(self):
        cur = self.pg_conn.cursor()
        for key in list(self.dirty_keys):
            val = self.redis.get(key)
            if val is not None:
                cur.execute(
                    'INSERT INTO data (key, value, updated_at) VALUES (%s, %s, now()) '
                    'ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at',
                    (key, val),
                )
                self.metrics.db_writes += 1
        cur.close()
        self.dirty_keys.clear()
