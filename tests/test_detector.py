import unittest
from cloudcompliance.drift.detector import DriftDetector


class TestDriftDetector(unittest.TestCase):
    def test_extract_tfstate_resources(self):
        detector = DriftDetector(tfstate_path="dummy.tfstate", endpoint_url="http://localhost:4566")
        mock_tfstate = {
            "resources": [
                {
                    "type": "aws_s3_bucket",
                    "name": "example",
                    "instances": [
                        {
                            "attributes": {
                                "bucket": "my-test-bucket",
                                "tags": {"Environment": "prod"}
                            }
                        }
                    ]
                }
            ]
        }
        resources = detector.extract_tfstate_resources(mock_tfstate)
        self.assertIn("aws_s3_bucket.example", resources)
        self.assertEqual(resources["aws_s3_bucket.example"]["bucket"], "my-test-bucket")


if __name__ == "__main__":
    unittest.main()
