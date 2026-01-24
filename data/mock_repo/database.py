"""Database utilities and connection pooling."""

from contextlib import contextmanager

import psycopg2.pool


class DatabaseManager:
    """Manages database connections and pooling."""

    def __init__(self, config):
        self.config = config
        self.pool = None

    def initialize_pool(self):
        """Initialize connection pool."""
        self.pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=self.config["pool_size"],
            host=self.config["host"],
            port=self.config["port"],
            database=self.config["database"],
            user=self.config["user"],
            password=self.config["password"],
            connect_timeout=self.config["timeout"],
        )

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        if self.pool is None:
            raise RuntimeError(
                "Connection pool not initialized. Call initialize_pool() first."
            )
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
