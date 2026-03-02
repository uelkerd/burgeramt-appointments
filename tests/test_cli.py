import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys

# Assume the main function is now in appointments.appointments
from appointments.appointments import main

class TestCLI(unittest.TestCase):

    @patch('appointments.appointments.watch_for_appointments', new_callable=AsyncMock)
    @patch('appointments.appointments.asyncio.run')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('appointments.appointments.ask_question')
    def test_main_with_all_args(self, mock_ask_question, mock_parse_args, mock_asyncio_run, mock_watch_for_appointments):
        # Configure mocks for a scenario where all arguments are provided
        mock_parse_args.return_value = MagicMock(
            id="test-id",
            email="test@example.com",
            url="https://service.berlin.de/test/",
            quiet=True,
            port=8080
        )
        
        main()

        # Assertions
        mock_parse_args.assert_called_once()
        mock_ask_question.assert_not_called()
        mock_watch_for_appointments.assert_called_once_with(
            "https://service.berlin.de/test/", "test@example.com", "test-id", 8080, True
        )
        # asyncio.run is called with the awaitable returned by mock_watch_for_appointments
        mock_asyncio_run.assert_called_once()

    @patch('appointments.appointments.watch_for_appointments', new_callable=AsyncMock)
    @patch('appointments.appointments.asyncio.run')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('appointments.appointments.ask_question')
    def test_main_with_missing_args_uses_ask_question(self, mock_ask_question, mock_parse_args, mock_asyncio_run, mock_watch_for_appointments):
        # Simulate missing URL and email, which should trigger ask_question
        mock_parse_args.return_value = MagicMock(
            id="test-id",
            email=None,  # Missing email
            url=None,    # Missing URL
            quiet=False,
            port=80
        )
        mock_ask_question.side_effect = ["https://service.berlin.de/asked/", "asked@example.com"]
        
        main()

        # Assertions
        mock_parse_args.assert_called_once()
        self.assertEqual(mock_ask_question.call_count, 2)
        mock_watch_for_appointments.assert_called_once_with(
            "https://service.berlin.de/asked/", "asked@example.com", "test-id", 80, False
        )
        mock_asyncio_run.assert_called_once()

    @patch('appointments.appointments.watch_for_appointments', new_callable=AsyncMock)
    @patch('appointments.appointments.asyncio.run')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('appointments.appointments.os.environ.get')
    @patch('appointments.appointments.ask_question') # Patch ask_question to ensure it's not called
    def test_main_with_env_vars(self, mock_ask_question, mock_env_get, mock_parse_args, mock_asyncio_run, mock_watch_for_appointments):
        # Simulate arguments coming from environment variables
        # mock_parse_args.return_value should reflect env vars being used if CLI args are None
        mock_parse_args.return_value = MagicMock(
            id="env-id",
            email="env@example.com",
            url="https://service.berlin.de/env/",
            quiet=False,
            port=80
        )
        mock_env_get.side_effect = {
            'BOOKING_TOOL_ID': 'env-id',
            'BOOKING_TOOL_EMAIL': 'env@example.com',
            'BOOKING_TOOL_URL': 'https://service.berlin.de/env/',
            # Ensure None is returned for other calls to os.environ.get
        }.get
        
        main()

        # Assertions
        mock_parse_args.assert_called_once()
        mock_ask_question.assert_not_called() # Should not be called as env vars provide values
        mock_watch_for_appointments.assert_called_once_with(
            "https://service.berlin.de/env/", "env@example.com", "env-id", 80, False
        )
        mock_asyncio_run.assert_called_once()

    @patch('appointments.appointments.watch_for_appointments', new_callable=AsyncMock)
    @patch('appointments.appointments.asyncio.run')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('appointments.appointments.ask_question')
    @patch('appointments.appointments.os.environ.get')
    def test_main_argument_precedence(self, mock_env_get, mock_ask_question, mock_parse_args, mock_asyncio_run, mock_watch_for_appointments):
        # CLI args should take precedence over env vars and ask_question
        mock_parse_args.return_value = MagicMock(
            id="cli-id",
            email="cli@example.com",
            url="https://service.berlin.de/cli/",
            quiet=True,
            port=8081
        )
        mock_env_get.side_effect = {
            'BOOKING_TOOL_ID': 'env-id',
            'BOOKING_TOOL_EMAIL': 'env@example.com',
            'BOOKING_TOOL_URL': 'https://service.berlin.de/env/',
        }.get
        mock_ask_question.side_effect = ["https://service.berlin.de/asked/", "asked@example.com"]

        main()

        # Assertions
        mock_parse_args.assert_called_once()
        mock_env_get.assert_called()
        mock_ask_question.assert_not_called()
        mock_watch_for_appointments.assert_called_once_with(
            "https://service.berlin.de/cli/", "cli@example.com", "cli-id", 8081, True
        )
        mock_asyncio_run.assert_called_once()