"""CSV schema, negative test fixtures, deterministic CLI artifact."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from site_screen.cli import main
from site_screen.io import REQUIRED, load_sites


class DataContractTests(unittest.TestCase):
    def test_example_sites_and_batch_output(self):
        path = Path(__file__).resolve().parents[1] / "data" / "synthetic_sites.csv"
        sites = load_sites(path)
        self.assertEqual(len(sites), 6)
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / "results.json"
            self.assertEqual(main([str(path), "--output", str(output)]), 0)
            a = output.read_bytes()
            self.assertEqual(main([str(path), "--output", str(output)]), 0)
            self.assertEqual(a, output.read_bytes())
            doc = json.loads(a)
            self.assertEqual(doc["input_site_count"], 6)
            self.assertTrue(doc["exclusions"])
            self.assertTrue(any(x["status"] == "source_limited_proxy"
                                for x in doc["results"]))
            self.assertTrue(any(x["status"] == "full_heat_demand_proxy"
                                for x in doc["results"]))
            self.assertTrue(any(x["status"] == "rejected"
                                for x in doc["results"]))

    def test_missing_column_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "sites.csv"
            f.write_text("site_id,source_supply_C\na,80\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid columns"):
                load_sites(f)

    def test_duplicate_site_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "test.csv"
            content = (Path(__file__).resolve().parents[1] / "data" / "synthetic_sites.csv").read_text()
            lines = content.splitlines()
            p.write_text("\n".join([lines[0], lines[1], lines[1]]) + "\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"duplicate"):
                load_sites(p)

    def test_extra_column_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "test.csv"
            original = (Path(__file__).resolve().parents[1] / "data" / "synthetic_sites.csv").read_text()
            lines = original.splitlines()
            p.write_text(lines[0] + ",unknown\n" + lines[1] + ",5\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"unexpected"):
                load_sites(p)

    def test_empty_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "test.csv"
            p.write_text("",encoding="utf-8")
            with self.assertRaises(ValueError):
                load_sites(p)


if __name__ == "__main__":
    unittest.main()
