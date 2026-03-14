import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, call

import fetchers.fina_indicator_vip_batch as vip_batch


class TestFinaIndicatorVipBatch(TestCase):
    def test_quarter_ends_between(self):
        self.assertEqual(
            vip_batch.quarter_ends_between("20240331", "20240630"),
            ["20240331", "20240630"],
        )
        self.assertEqual(
            vip_batch.quarter_ends_between("20240331", "20240501"),
            ["20240331"],
        )
        self.assertEqual(
            vip_batch.quarter_ends_between("20240101", "20241231"),
            ["20240331", "20240630", "20240930", "20241231"],
        )

    def test_progress_io_roundtrip(self):
        original_progress_file = vip_batch.PROGRESS_FILE
        original_progress_log = vip_batch.PROGRESS_LOG
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                vip_batch.PROGRESS_FILE = tmp_path / "progress.json"
                vip_batch.PROGRESS_LOG = tmp_path / "progress.log"

                vip_batch.save_progress({"20240331"})
                vip_batch.append_progress("20240630")

                loaded = vip_batch.load_progress()
                self.assertEqual(loaded, {"20240331", "20240630"})
        finally:
            vip_batch.PROGRESS_FILE = original_progress_file
            vip_batch.PROGRESS_LOG = original_progress_log

    def test_run_vip_calls_fetch(self):
        original_progress_file = vip_batch.PROGRESS_FILE
        original_progress_log = vip_batch.PROGRESS_LOG
        original_save_every = vip_batch.SAVE_EVERY
        original_data_dir = vip_batch.DATA_DIR
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                data_dir = tmp_path / "data"
                vip_batch.DATA_DIR = data_dir
                vip_batch.PROGRESS_FILE = data_dir / "progress.json"
                vip_batch.PROGRESS_LOG = data_dir / "progress.log"
                vip_batch.SAVE_EVERY = 1

                side_effects = [Exception("fail"), 1]
                with patch.object(vip_batch, "fetch_and_save", side_effect=side_effects) as mock_fetch:
                    with patch.object(vip_batch.time, "sleep"):
                        vip_batch.run_vip("20240331", "20240630", delay=0, resume=False)

                mock_fetch.assert_has_calls(
                    [call(period="20240331", use_vip=True), call(period="20240630", use_vip=True)],
                    any_order=False,
                )

                data = json.loads(vip_batch.PROGRESS_FILE.read_text(encoding="utf-8"))
                self.assertEqual(set(data["processed"]), {"20240630"})
                self.assertTrue(vip_batch.PROGRESS_LOG.exists())
        finally:
            vip_batch.PROGRESS_FILE = original_progress_file
            vip_batch.PROGRESS_LOG = original_progress_log
            vip_batch.SAVE_EVERY = original_save_every
            vip_batch.DATA_DIR = original_data_dir
