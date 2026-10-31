import unittest
from cloudcompliance.report import evaluate_controls, load_controls, extract_resources


class TestReport(unittest.TestCase):
    def test_load_controls(self):
        controls = load_controls()
        self.assertIn("CC6.1", controls)
        self.assertIn("CC6.2", controls)
        self.assertEqual(len(controls), 10)

    def test_evaluate_controls_all_pass(self):
        controls = load_controls()
        mock_resources = []
        for ctrl in controls.values():
            for res_type in ctrl["resources"]:
                mock_resources.append({"type": res_type, "name": f"mock_{res_type}"})

        results = evaluate_controls(mock_resources, controls)
        for control_id, result in results.items():
            self.assertEqual(result["status"], "PASS")

    def test_evaluate_controls_partial_fail(self):
        controls = load_controls()
        mock_resources = [{"type": "aws_vpc", "name": "mock_vpc"}]
        results = evaluate_controls(mock_resources, controls)

        self.assertEqual(results["CC6.1"]["status"], "PARTIAL")
        self.assertEqual(results["CC6.2"]["status"], "FAIL")

    def test_evaluate_controls_aws_pure_pass(self):
        controls = load_controls()
        mock_resources = []
        for ctrl in controls.values():
            for res_type in ctrl["resources"]:
                if res_type.startswith("aws_"):
                    mock_resources.append({"type": res_type, "name": f"mock_{res_type}"})

        results = evaluate_controls(mock_resources, controls, provider="aws")
        for control_id, result in results.items():
            self.assertEqual(result["status"], "PASS")

    def test_extract_resources(self):
        mock_state = {
            "resources": [
                {
                    "type": "aws_s3_bucket",
                    "name": "my_bucket",
                    "module": "root",
                    "instances": [{"attributes": {"tags": {"Environment": "test"}}}]
                }
            ]
        }
        extracted = extract_resources(mock_state)
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0]["type"], "aws_s3_bucket")
        self.assertEqual(extracted[0]["name"], "my_bucket")
        self.assertEqual(extracted[0]["tags"], {"Environment": "test"})


if __name__ == "__main__":
    unittest.main()
