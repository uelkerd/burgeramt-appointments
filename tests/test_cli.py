import unittest
from unittest.mock import patch, AsyncMock
import sys

# Assume the main function is now in appointments.appointments
from appointments.appointments import main


class TestCLI(unittest.TestCase):

    @patch('appointments.appointments.watch_for_appointments', new_callable=AsyncMock)
    @patch('appointments.appointments.asyncio.run')
    @patch('sys.argv', ['appointments', '--id', 'test-id', '--email', 'test@example.com', '--url', 'https://service.berlin.de/test/', '--quiet', '--port', '8080'])
    @patch('appointments.appointments.ask_question')
    def test_main_with_all_args(
        self, mock_ask_question, mock_asyncio_run, mock_watch_for_appointments
    ):
        main()

        # Assertions
        mock_ask_question.assert_not_called()
        mock_watch_for_appointments.assert_called_once_with(
            "https://service.berlin.de/test/", "test@example.com", "test-id", 8080, True
        )
        mock_asyncio_run.assert_called_once()

    @patch('appointments.appointments.watch_for_appointments', new_callable=AsyncMock)
    @patch('appointments.appointments.asyncio.run')
    @patch('sys.argv', ['appointments'])
    @patch('appointments.appointments.ask_question')
    def test_main_with_missing_args_uses_ask_question(
        self, mock_ask_question, mock_asyncio_run, mock_watch_for_appointments
    ):
        # Simulate missing URL and email, which should trigger ask_question
        mock_ask_question.side_effect = ["https://service.berlin.de/asked/", "asked@example.com"]

        main()

        # Assertions
        self.assertEqual(mock_ask_question.call_count, 2)
        mock_watch_for_appointments.assert_called_once_with(
            "https://service.berlin.de/asked/", "asked@example.com", "", 80, False
        )
        mock_asyncio_run.assert_called_once()

    @patch('appointments.appointments.watch_for_appointments', new_callable=AsyncMock)
    @patch('appointments.appointments.asyncio.run')
    @patch('sys.argv', ['appointments'])
    @patch('appointments.appointments.os.environ.get')
    @patch('appointments.appointments.ask_question')
    def test_main_with_env_vars(
        self, mock_ask_question, mock_env_get, mock_asyncio_run, mock_watch_for_appointments
    ):
        # Simulate arguments coming from environment variables
        def mock_getenv(key, default=None):
            env_vars = {
                'BOOKING_TOOL_ID': 'env-id',
                'BOOKING_TOOL_EMAIL': 'env@example.com',
                'BOOKING_TOOL_URL': 'https://service.berlin.de/env/',
            }
            return env_vars.get(key, default)

        mock_env_get.side_effect = mock_getenv

        main()

        # Assertions
        mock_ask_question.assert_not_called()
        mock_watch_for_appointments.assert_called_once_with(
            "https://service.berlin.de/env/", "env@example.com", "env-id", 80, False
        )
        mock_asyncio_run.assert_called_once()

    @patch('appointments.appointments.watch_for_appointments', new_callable=AsyncMock)
    @patch('appointments.appointments.asyncio.run')
    @patch('sys.argv', ['appointments', '--id', 'cli-id', '--email', 'cli@example.com', '--url', 'https://service.berlin.de/cli/', '--quiet', '--port', '8081'])
    @patch('appointments.appointments.ask_question')
    @patch('appointments.appointments.os.environ.get')
    def test_main_argument_precedence(
        self, mock_env_get, mock_ask_question, mock_asyncio_run, mock_watch_for_appointments
    ):
        # CLI args should take precedence over env vars and ask_question
        def mock_getenv(key, default=None):
            env_vars = {
                'BOOKING_TOOL_ID': 'env-id',
                'BOOKING_TOOL_EMAIL': 'env@example.com',
                'BOOKING_TOOL_URL': 'https://service.berlin.de/env/',
            }
            return env_vars.get(key, default)

        mock_env_get.side_effect = mock_getenv

        main()

        # Assertions
        mock_env_get.assert_called()
        mock_ask_question.assert_not_called()
        mock_watch_for_appointments.assert_called_once_with(
            "https://service.berlin.de/cli/", "cli@example.com", "cli-id", 8081, True
        )
        mock_asyncio_run.assert_called_once()
