import unittest
from unittest.mock import patch, MagicMock

# Assume the main function is now in appointments.appointments
from appointments.appointments import main


class TestCLI(unittest.TestCase):

    def setUp(self):
        # Use explicit MagicMock for the async function to allow identity comparison
        # in mock_asyncio_run.assert_called_once_with(mock_watch.return_value)
        self.mock_watch_patcher = patch(
            'appointments.appointments.watch_for_appointments', new=MagicMock()
        )
        self.mock_run_patcher = patch('appointments.appointments.asyncio.run')
        self.mock_ask_patcher = patch('appointments.appointments.ask_question', autospec=True)
        self.mock_env_patcher = patch('appointments.appointments.os.environ.get')

        self.mock_watch = self.mock_watch_patcher.start()
        self.mock_run = self.mock_run_patcher.start()
        self.mock_ask = self.mock_ask_patcher.start()
        self.mock_env = self.mock_env_patcher.start()
        # Default os.environ.get to return None so defaults work as expected
        self.mock_env.return_value = None

    def tearDown(self):
        self.mock_watch_patcher.stop()
        self.mock_run_patcher.stop()
        self.mock_ask_patcher.stop()
        self.mock_env_patcher.stop()

    def test_main_with_all_args(self):
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
