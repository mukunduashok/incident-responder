"""Payment processing service."""

import psycopg2
from datetime import datetime


class PaymentProcessor:
    """Handles payment transactions."""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.db_pool = self._create_pool()
    
    def _create_pool(self):
        """Create database connection pool."""
        return psycopg2.pool.SimpleConnectionPool(
            1, 10,
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )
    
    def process_payment(self, transaction_id, amount, user_id):
        """Process a payment transaction."""
        conn = self.db_pool.getconn()
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO payments (transaction_id, amount, user_id, status, created_at)
                VALUES (%s, %s, %s, 'pending', %s)
            """
            # Added timeout parameter
            cursor.execute(query, (transaction_id, amount, user_id, datetime.now()), timeout=5)
            conn.commit()
            return {'status': 'success', 'transaction_id': transaction_id}
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.db_pool.putconn(conn)
