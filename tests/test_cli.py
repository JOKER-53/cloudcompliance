import unittest
from unittest.mock import patch
import sys

from cloudcompliance.cli import main


class TestCLI(unittest.TestCase):
    @patch("cloudcompliance.cli.load_tfstate")
    @patch("cloudcompliance.cli.print_report")
    def test_cli_report_default(self, mock_print_report, mock_load_tfstate):
        mock_load_tfstate.return_value = {"resources": []}
        test_args = ["cloudcompliance", "report", "--framework", "soc2"]
        with patch.object(sys, "argv", test_args):
            main()
            self.assertTrue(mock_print_report.called)

    @patch("cloudcompliance.history.show_history")
    def test_cli_history(self, mock_show_history):
        test_args = ["cloudcompliance", "history", "--limit", "5"]
        with patch.object(sys, "argv", test_args):
            main()
            mock_show_history.assert_called_once_with(limit=5)


if __name__ == "__main__":
    unittest.main()
