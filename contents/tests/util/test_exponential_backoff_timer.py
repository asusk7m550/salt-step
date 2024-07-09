import sys, os
import unittest
from unittest.mock import patch

sys.path.append(os.getcwd())
from contents.util.exponential_backoff_timer import ExponentialBackoffTimer


class TestExponentialBackoffTimer(unittest.TestCase):

    def test_initialize(self):
        delay_step = 1
        maximum_delay = 30
        timer = ExponentialBackoffTimer(delay_step, maximum_delay)

        self.assertEqual(timer.delay_step, delay_step)
        self.assertEqual(timer.maximum_delay, maximum_delay)

    @patch.object(ExponentialBackoffTimer, 'sleep')
    def test_wait_for_next(self, mock_sleep):
        delay_step = 1
        maximum_delay = 300
        expected_backoff = [1, 3, 7, 15, 31, 63, 127, 255, 300, 300]
        timer = ExponentialBackoffTimer(delay_step, maximum_delay)

        for _ in range(10):
            timer.wait_for_next()

        sleep_values = [call[0][0] for call in mock_sleep.call_args_list]
        self.assertEqual(sleep_values, expected_backoff)

    @patch.object(ExponentialBackoffTimer, 'sleep')
    def test_interrupted(self, mock_sleep):
        def side_effect(delay):
            raise KeyboardInterrupt

        mock_sleep.side_effect = side_effect

        timer = ExponentialBackoffTimer(1, 300)

        with self.assertRaises(InterruptedError):
            for _ in range(10):
                timer.wait_for_next()

        self.assertEqual(mock_sleep.call_count, 1)
