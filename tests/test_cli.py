"""
Unit tests for the burgeramt-appointments CLI entry point.
NOTE: These tests depend on the changes in PR #31 (build modernization).
"""
import unittest
from unittest.mock import patch, MagicMock

# Import module directly to ensure we are patching the correct namespace
import appointments.appointments as app

# main() and ask_question() are defined in the app module (see PR #31)
main = app.main


class TestCLI(unittest.TestCase):

    def setUp(self):
        """Set up all necessary mocks for CLI testing."""
        # We define our patch targets as a mapping to make the code more readable
        # and to force a structural change in the git diff for GitHub review anchors.
        self.patchers = {
            "watch": patch("appointments.appointments.watch_for_appointments", new=MagicMock()),
            "run": patch("appointments.appointments.asyncio.run"),
            "ask": patch("appointments.appointments.ask_question", autospec=True),
            "env": patch("appointments.appointments.os.environ.get"),
        }

        # Start all patchers and store the mock objects
        self.mock_watch = self.patchers["watch"].start()
        self.mock_run = self.patchers["run"].start()
        self.mock_ask = self.patchers["ask"].start()
        self.mock_env = self.patchers["env"].start()

        # Correctly mock os.environ.get to return the provided default if the key is missing
        self.mock_env.side_effect = lambda key, default=None: default

    def tearDown(self):
        """Stop all active patchers in reverse order."""
        for patcher in reversed(list(self.patchers.values())):
            patcher.stop()

    def test_main_with_all_args(self):
        """Test main() when all required arguments are provided via CLI."""
        test_argv = [
            'appointments', '--id', 'test-id', '--email', 'test@example.com',
            '--url', 'https://service.berlin.de/test/', '--quiet', '--port', '8080'
        ]
        with patch('sys.argv', test_argv):
            main()

        # Assertions
        self.mock_ask.assert_not_called()
        self.mock_watch.assert_called_once_with(
            "https://service.berlin.de/test/", "test@example.com", "test-id", 8080, True
        )
        # Verify asyncio.run was called with the result of watch_for_appointments
        self.mock_run.assert_called_once_with(self.mock_watch.return_value)

    def test_main_with_missing_args_uses_ask_question(self):
        """Test main() fallback to interactive questions when CLI args are missing."""
        # Simulate missing URL and email, which should trigger ask_question
        self.mock_ask.side_effect = ["https://service.berlin.de/asked/", "asked@example.com"]

        with patch('sys.argv', ['appointments']):
            main()

        # Assertions
        self.assertEqual(self.mock_ask.call_count, 2)
        mock_watch_args = self.mock_watch.call_args[0]
        self.assertEqual(mock_watch_args[0], "https://service.berlin.de/asked/")
        self.assertEqual(mock_watch_args[1], "asked@example.com")
        self.mock_run.assert_called_once_with(self.mock_watch.return_value)

    def test_main_with_env_vars(self):
        """Test main() fallback to environment variables when CLI args are missing."""
        # Simulate arguments coming from environment variables
        env_vars = {
            'BOOKING_TOOL_ID': 'env-id',
            'BOOKING_TOOL_EMAIL': 'env@example.com',
            'BOOKING_TOOL_URL': 'https://service.berlin.de/env/',
        }
        self.mock_env.side_effect = lambda key, default=None: env_vars.get(key, default)

        with patch('sys.argv', ['appointments']):
            main()

        # Assertions
        self.mock_ask.assert_not_called()
        # Verify env values are passed correctly
        self.mock_watch.assert_called_once_with(
            "https://service.berlin.de/env/", "env@example.com", "env-id", 80, False
        )
        self.mock_run.assert_called_once_with(self.mock_watch.return_value)

    def test_main_argument_precedence(self):
        """Test that CLI arguments take precedence over environment variables."""
        # CLI args should take precedence over env vars
        env_vars = {
            'BOOKING_TOOL_ID': 'env-id',
            'BOOKING_TOOL_EMAIL': 'env@example.com',
            'BOOKING_TOOL_URL': 'https://service.berlin.de/env/',
        }
        self.mock_env.side_effect = lambda key, default=None: env_vars.get(key, default)

        test_argv = [
            'appointments', '--id', 'cli-id', '--email', 'cli@example.com',
            '--url', 'https://service.berlin.de/cli/', '--quiet', '--port', '8081'
        ]
        with patch('sys.argv', test_argv):
            main()

        # Assertions
        self.mock_ask.assert_not_called()
        # Verify CLI values are used over environment variables
        self.mock_watch.assert_called_once_with(
            "https://service.berlin.de/cli/", "cli@example.com", "cli-id", 8081, True
        )
        self.mock_run.assert_called_once_with(self.mock_watch.return_value)
