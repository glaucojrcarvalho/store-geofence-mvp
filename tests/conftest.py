import os
import time
import pytest
import psycopg2
import traceback

from app.core.config import settings


def _try_connect(host, port, dbname, user, password):
    conn = None
    try:
        conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
        return conn
    except Exception:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        raise


def _wait_for_companies_table(timeout: int) -> (bool, str):
    """Poll the database until the companies table exists or timeout.

    Tries multiple candidate hosts to be resilient across CI runner/service networking.
    Returns (ok, last_error_message).
    """
    deadline = time.time() + timeout
    last_err = None
    candidate_hosts = []
    # Primary: respect configured host
    if settings.POSTGRES_HOST:
        candidate_hosts.append(str(settings.POSTGRES_HOST))
    # Common possibilities
    candidate_hosts.extend(["127.0.0.1", "localhost", "db"])
    # dedupe while preserving order
    seen = set()
    candidate_hosts = [h for h in candidate_hosts if not (h in seen or seen.add(h))]

    while time.time() < deadline:
        for host in candidate_hosts:
            try:
                conn = _try_connect(host, settings.POSTGRES_PORT, settings.POSTGRES_DB, settings.POSTGRES_USER, settings.POSTGRES_PASSWORD)
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT to_regclass('public.companies')")
                    res = cur.fetchone()[0]
                    cur.close()
                    conn.close()
                    if res is not None:
                        return True, f"connected_host={host}"
                except Exception:
                    last_err = traceback.format_exc()
                    try:
                        conn.close()
                    except Exception:
                        pass
            except Exception:
                last_err = traceback.format_exc()
        time.sleep(1)
    return False, (last_err or "timeout waiting for DB")


@pytest.fixture(scope="session", autouse=True)
def e2e_db_ready():
    """Ensure DB is available and migrations are applied before running tests.

    This fixture runs once per test session and will attempt an alembic upgrade
    and then poll the database until the `companies` table exists.
    If the database does not become ready within the timeout, pytest will exit
    and the error will include the last connection exception to aid debugging.
    """
    timeout = int(os.getenv("E2E_DB_WAIT", "240"))

    # Print environment for debugging in CI logs
    print("[e2e_db_ready] Using DB host from settings.POSTGRES_HOST:", settings.POSTGRES_HOST)
    print("[e2e_db_ready] DATABASE_URL:", getattr(settings, 'DATABASE_URL', None))

    # Try to run alembic programmatically; ignore non-fatal failures and continue to polling
    try:
        from alembic.config import Config
        from alembic import command
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cfg_path = os.path.join(repo_root, "alembic.ini")
        print(f"[e2e_db_ready] Running alembic upgrade head with config: {cfg_path}")
        cfg = Config(cfg_path)
        # Ensure the alembic config uses the same DATABASE_URL as settings
        cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.upgrade(cfg, "head")
        print("[e2e_db_ready] alembic upgrade head finished")
    except Exception:
        # best-effort: migrations may have been applied by CI step; capture exception for logs
        print("[e2e_db_ready] alembic programmatic upgrade failed (continuing to poll):")
        traceback.print_exc()

    ok, info = _wait_for_companies_table(timeout)
    if not ok:
        print("[e2e_db_ready] Database did not become ready in time. Last error:\n", info)
        pytest.exit("Database not ready or migrations not applied in time")
    print("[e2e_db_ready] Database ready and migrations applied (", info, ")")
    yield
