import json
import tempfile
import unittest
from pathlib import Path

from cloudcompliance.history import get_db, save_score, export_history


class TestHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_history.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_db_creates_table(self):
        conn = get_db(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compliance_history';")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "compliance_history")

    def test_save_and_export_score(self):
        report_data = {
            "compliance_score": 100,
            "total_resources": 15,
            "controls": {
                "CC6.1": {"status": "PASS"},
                "CC6.2": {"status": "PASS"},
            }
        }
        report_path = Path(self.temp_dir.name) / "report.json"
        with open(report_path, "w") as f:
            json.dump(report_data, f)

        save_score(report_path, db_path=self.db_path)

        export_path = Path(self.temp_dir.name) / "export.json"
        exported = export_history(output_path=export_path, db_path=self.db_path)

        self.assertEqual(exported["entry_count"], 1)
        self.assertEqual(exported["entries"][0]["score"], 100)
        self.assertEqual(exported["entries"][0]["controls_passing"], 2)


if __name__ == "__main__":
    unittest.main()
