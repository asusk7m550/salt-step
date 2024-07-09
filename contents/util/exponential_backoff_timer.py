import time
import math


class ExponentialBackoffTimer:
    def __init__(self, delay_step, maximum_delay):
        """
        Creates a backoff timer using the given delay_step and maximum_delay

        :param delay_step: A multiplier value (in ms) for the amount to sleep for.
        :param maximum_delay: The maximum amount for the sleep value (in ms)
        """
        self.delay_step = delay_step
        self.maximum_delay = maximum_delay
        self.count = 2
        self.next_sleep_amount = self.delay_step

    def wait_for_next(self):
        """
        Calls time.sleep for an appropriate length of time depending on how many
        times this method has already been invoked.

        Uses the default E(c) = (2^x-1)/2 formula.

        :raises InterruptedError: if the sleep is interrupted.
        """
        try:
            self.sleep(self.next_sleep_amount)
            if self.next_sleep_amount < self.maximum_delay:
                self.next_sleep_amount = (math.pow(2, self.count) - 1) * self.delay_step
                self.count += 1
            self.next_sleep_amount = min(self.maximum_delay, self.next_sleep_amount)
        except KeyboardInterrupt:
            raise InterruptedError()

    def sleep(self, delay):  # pragma: no cover
        """
        Sleeps for the specified amount of time.

        :param delay: The amount of time to sleep in seconds.
        """
        time.sleep(delay/1000.0)  # convert to seconds
