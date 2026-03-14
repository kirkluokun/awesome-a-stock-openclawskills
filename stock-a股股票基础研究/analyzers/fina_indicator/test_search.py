import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzers.fina_indicator import search


class TestFinaIndicatorSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, db_path = tempfile.mkstemp(suffix=".db")
        Path(db_path).unlink(missing_ok=True)
        cls.db_path = Path(db_path)
        schema_path = Path(__file__).resolve().parent / "schema.sql"
        schema = schema_path.read_text(encoding="utf-8")
        conn = sqlite3.connect(str(cls.db_path))
        try:
            conn.executescript(schema)
            conn.execute(
                """
                INSERT INTO fina_indicator (
                    ts_code, ann_date, end_date, roe, payload_json, source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "000001.SZ",
                    "20240101",
                    "20231231",
                    0.12,
                    '{"eps": 2.5}',
                    "unit-test",
                    "2024-01-01 00:00:00",
                    "2024-01-01 00:00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO fina_indicator (
                    ts_code, ann_date, end_date, roe, payload_json, source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "000001.SZ",
                    "20240201",
                    "20240331",
                    0.15,
                    "{bad-json",
                    "unit-test",
                    "2024-02-01 00:00:00",
                    "2024-02-01 00:00:00",
                ),
            )
            conn.commit()
        finally:
            conn.close()

        def connect_override():
            conn = sqlite3.connect(str(cls.db_path))
            conn.row_factory = sqlite3.Row
            return conn

        cls.connect_patch = patch(
            "analyzers.fina_indicator.search.connect",
            side_effect=connect_override,
        )
        cls.connect_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.connect_patch.stop()
        if cls.db_path.exists():
            cls.db_path.unlink()

    def test_history_limit_must_be_int(self):
        with self.assertRaises(ValueError):
            search.get_fina_indicator_history(
                "000001.SZ",
                limit="1; DROP TABLE fina_indicator",
            )

    def test_get_fina_indicator_skips_bad_payload(self):
        record = search.get_fina_indicator("000001.SZ")
        self.assertIsNotNone(record)
        self.assertEqual(record["end_date"], "20240331")
        self.assertEqual(record["roe"], 0.15)

    def test_get_field_value_does_not_parse_payload_again(self):
        with patch(
            "analyzers.fina_indicator.search.get_fina_indicator",
            return_value={"payload_json": "{bad", "eps": "3.5"},
        ), patch(
            "analyzers.fina_indicator.search.json.loads",
            side_effect=AssertionError("json.loads should not be called"),
        ):
            value = search.get_field_value("000001.SZ", "eps")
            self.assertEqual(value, 3.5)
