"""Database configuration and utilities."""

DATABASE_CONFIG = {
    'host': 'prod-db',
    'port': 5432,
    'database': 'payments',
    'user': 'app_user',
    'password': 'secure_password',
    'pool_size': 10,
    'timeout': 5  # Reduced from 30 to 5 seconds
}
