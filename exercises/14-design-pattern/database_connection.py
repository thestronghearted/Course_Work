"""Database connection manager — refactored with the Factory pattern (Exercise 14).

The original ``DatabaseConnection.connect`` was a long ``if db_type == ...`` chain
that mixed the selection of a database type with the per-type connection logic.
Adding a new database meant editing that method (violating Open/Closed).

This refactor applies the **Factory pattern**:
  * ``DatabaseConnector`` — abstract base defining ``connect(config)``.
  * one concrete connector per database (MySQL, PostgreSQL, MongoDB, Redis),
    each owning only its own connection-string logic.
  * ``ConnectorFactory`` — maps a ``db_type`` string to the right connector, and
    raises ``ValueError`` for unknown types.

``DatabaseConnection`` keeps the same public interface (so existing callers and
tests are unchanged); ``connect()`` now delegates to a factory-created connector.
Adding a new database is now just a new connector class + one registry entry.
"""

from abc import ABC, abstractmethod


class DatabaseConnector(ABC):
    """Strategy interface: build and 'open' a connection for one database type."""

    @abstractmethod
    def connect(self, config):
        """Print/establish the connection for ``config`` (a DatabaseConnection)."""


class MySqlConnector(DatabaseConnector):
    def connect(self, config):
        cs = f"mysql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        cs += f"?charset={config.charset}"
        cs += f"&connectionTimeout={config.connection_timeout}"
        if config.use_ssl:
            cs += "&useSSL=true"
        print(f"MySQL Connection: {cs}")


class PostgreSqlConnector(DatabaseConnector):
    def connect(self, config):
        cs = f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        if config.use_ssl:
            cs += "?sslmode=require"
        print(f"PostgreSQL Connection: {cs}")


class MongoDbConnector(DatabaseConnector):
    def connect(self, config):
        cs = f"mongodb://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        cs += f"?retryAttempts={config.retry_attempts}"
        cs += f"&poolSize={config.pool_size}"
        if config.use_ssl:
            cs += "&ssl=true"
        print(f"MongoDB Connection: {cs}")


class RedisConnector(DatabaseConnector):
    def connect(self, config):
        print(f"Redis Connection: {config.host}:{config.port}/{config.database}")


class ConnectorFactory:
    """Creates the correct :class:`DatabaseConnector` for a database type."""

    _registry = {
        'mysql': MySqlConnector,
        'postgresql': PostgreSqlConnector,
        'mongodb': MongoDbConnector,
        'redis': RedisConnector,
    }

    @classmethod
    def create(cls, db_type):
        try:
            connector_cls = cls._registry[db_type]
        except KeyError:
            raise ValueError(f"Unsupported database type: {db_type}")
        return connector_cls()


class DatabaseConnection:
    """Client/config object. Public interface is unchanged from the original."""

    def __init__(self, db_type, host, port, username, password, database,
                 use_ssl=False, connection_timeout=30, retry_attempts=3,
                 pool_size=5, charset='utf8'):
        self.db_type = db_type
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.use_ssl = use_ssl
        self.connection_timeout = connection_timeout
        self.retry_attempts = retry_attempts
        self.pool_size = pool_size
        self.charset = charset
        self.connection = None

    def connect(self):
        print(f"Connecting to {self.db_type} database...")
        connector = ConnectorFactory.create(self.db_type)  # raises ValueError if unknown
        connector.connect(self)
        print("Connection successful!")
        return self.connection


if __name__ == "__main__":
    DatabaseConnection(db_type='mysql', host='localhost', port=3306,
                       username='db_user', password='password123',
                       database='app_db', use_ssl=True).connect()
    DatabaseConnection(db_type='mongodb', host='mongodb.example.com', port=27017,
                       username='mongo_user', password='mongo123',
                       database='analytics', pool_size=10, retry_attempts=5).connect()
