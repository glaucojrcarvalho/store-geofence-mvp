import os
import time
import pytest
import psycopg2

from app.core.config import settings


def _wait_for_companies_table(timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            conn = psycopg2.connect(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                dbname=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
            )
            try:
                cur = conn.cursor()
                cur.execute("SELECT to_regclass('public.companies')")
                res = cur.fetchone()[0]
                cur.close()
                conn.close()
                if res is not None:
                    return True
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(1)
    return False


@pytest.fixture(scope="session", autouse=True)
def e2e_db_ready():
    """Ensure DB is available and migrations are applied before running tests.

    This fixture runs once per test session and will attempt an alembic upgrade
    and then poll the database until the `companies` table exists.
    If the database does not become ready within the timeout, pytest will exit.
    """
    timeout = int(os.getenv("E2E_DB_WAIT", "180"))

    # Try to run alembic programmatically; ignore failures and continue to polling
    try:
        from alembic.config import Config
        from alembic import command
        here = os.path.abspath(os.path.dirname(__file__))
        cfg_path = os.path.join(here, "..", "alembic.ini")
        cfg = Config(cfg_path)
        cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.upgrade(cfg, "head")
    except Exception:
        # best-effort: migrations may have been applied by CI step
        pass

    ok = _wait_for_companies_table(timeout)
    if not ok:
        pytest.exit("Database not ready or migrations not applied in time")
    yield

