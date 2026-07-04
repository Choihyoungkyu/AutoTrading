import sqlite3
import json
import pandas as pd
from datetime import date
from pathlib import Path

DB_PATH = Path("data/stock_data.db")


class DataStore:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(str(self.db_path))

    def ping(self) -> bool:
        try:
            with self._connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def save(self, df: pd.DataFrame, table: str) -> int:
        if df.empty:
            return 0
        with self._connect() as conn:
            df.to_sql(table, conn, if_exists="append", index=False)
        return len(df)

    def load(self, table: str, code: str = None,
             start: str = None, end: str = None) -> pd.DataFrame:
        with self._connect() as conn:
            query = f"SELECT * FROM {table}"
            conditions = []
            params = []
            if code:
                conditions.append("code = ?")
                params.append(code)
            if start:
                conditions.append("date >= ?")
                params.append(start)
            if end:
                conditions.append("date <= ?")
                params.append(end)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY date"
            return pd.read_sql_query(query, conn, params=params)

    def export_csv(self, table: str, path: str) -> str:
        df = self.load(table)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path

    def _ensure_financial_table(self, conn):
        conn.execute(
            "CREATE TABLE IF NOT EXISTS financial_cache "
            "(code TEXT, date TEXT, data TEXT, PRIMARY KEY (code, date))"
        )

    def save_financial(self, code: str, data: dict) -> None:
        with self._connect() as conn:
            self._ensure_financial_table(conn)
            conn.execute(
                "INSERT OR REPLACE INTO financial_cache VALUES (?, ?, ?)",
                (code, str(date.today()), json.dumps(data))
            )

    def load_financial(self, code: str) -> dict | None:
        with self._connect() as conn:
            self._ensure_financial_table(conn)
            row = conn.execute(
                "SELECT data FROM financial_cache WHERE code=? AND date=?",
                (code, str(date.today()))
            ).fetchone()
            if row is None:
                # 오늘자 캐시가 없으면 가장 최근 캐시로 폴백(시드 데이터 유지).
                # 실시간 재무 소스가 비어도 재무 카드가 깨지지 않도록 한다.
                row = conn.execute(
                    "SELECT data FROM financial_cache WHERE code=? ORDER BY date DESC LIMIT 1",
                    (code,)
                ).fetchone()
        return json.loads(row[0]) if row else None

    def _ensure_news_cache_table(self, conn):
        conn.execute(
            "CREATE TABLE IF NOT EXISTS news_cache "
            "(code TEXT, date TEXT, data TEXT, PRIMARY KEY (code, date))"
        )

    def save_news(self, code: str, data: dict) -> None:
        with self._connect() as conn:
            self._ensure_news_cache_table(conn)
            conn.execute(
                "INSERT OR REPLACE INTO news_cache VALUES (?, ?, ?)",
                (code, str(date.today()), json.dumps(data))
            )

    def load_news(self, code: str) -> dict | None:
        with self._connect() as conn:
            self._ensure_news_cache_table(conn)
            row = conn.execute(
                "SELECT data FROM news_cache WHERE code=? AND date=?",
                (code, str(date.today()))
            ).fetchone()
            if row is None:
                # 뉴스 수집 실패 시 가장 최근 캐시로 폴백(PRD: 크롤링 실패가 장애로 이어지지 않게).
                row = conn.execute(
                    "SELECT data FROM news_cache WHERE code=? ORDER BY date DESC LIMIT 1",
                    (code,)
                ).fetchone()
        return json.loads(row[0]) if row else None
