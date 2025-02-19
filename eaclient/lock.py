import logging
import time

from eaclient import exceptions, util

LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))


class RetryLock:
    """
    Context manager for gaining exclusive access to the lock file.

    Create a lock file if absent. The lock file will contain a pid of the
    running process, and a customer-visible description of the lock holder.

    The RetryLock will try several times to acquire the lock before giving up.
    The number of times to try and how long to sleep in between tries is
    configurable.

    :param lock_holder: String with the service name or command which is
        holding the lock. This lock_holder string will be customer visible in
        status.json.
    :param sleep_time: Number of seconds to sleep before retrying if the lock
        is already held.
    :param max_retries: Maximum number of times to try to grab the lock before
        giving up and raising a LockHeldError.
    :raises: LockHeldError if lock is held after (sleep_time * max_retries)
    """

    def __init__(
        self,
        *_args,
        lock_holder: str,
        sleep_time: int = 10,
        max_retries: int = 12
    ):
        self.lock_holder = lock_holder
        self.sleep_time = sleep_time
        self.max_retries = max_retries

    def grab_lock(self):
        LOG.debug("require lock action")

    def __enter__(self):
        LOG.debug("spin lock starting for %s", self.lock_holder)
        tries = 0
        while True:
            try:
                self.grab_lock()
                break
            except exceptions.LockHeldError as e:
                LOG.debug(
                    "RetryLock Attempt %d. %s. Spinning...", tries + 1, e.msg
                )
                tries += 1
                if tries >= self.max_retries:
                    raise e
                else:
                    time.sleep(self.sleep_time)

    def __exit__(self, _exc_type, _exc_value, _traceback):
        LOG.debug("release lock")
