"""Database connection pooling."""


from contextlib import contextmanager
import importlib
import tomllib

from psycopg2.pool import SimpleConnectionPool


_resources = importlib.resources.files('stargaze.resources')


class SessionFactory:

    _instance = None

    def __init__(self, credentials):
        self.pool = SimpleConnectionPool(
            minconn=1,
            maxconn=3,
            **credentials
        )
        self.open = True

    @classmethod
    def get_instance(cls):
        """Returns a session factory instance."""
        if cls._instance is None:
            with open(_resources/'credentials.toml', 'rb') as credentials_file:
                credentials = tomllib.load(credentials_file)
            cls._instance = SessionFactory(credentials)
        return cls._instance

    def execute(self, transaction):
        """Executes given transaction logic."""
        with session_scope(self) as session:
            return transaction(session)

    def get_session(self):
        """Acquires and returns a session."""
        return self.pool.getconn()

    def put_session(self, session):
        """Releases session."""
        return self.pool.putconn(session)

    def close(self):
        """Closes connection pool."""
        if self.open:
            self.pool.closeall()
            self.open = False

    @contextmanager
    def session_scope(self):
        """Context manager for a session."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as exc:
            session.rollback()
            raise exc
        finally:
            self.put_session(session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        if self.open:
            print("Session factory was not closed properly, closing now")
            self.close()
