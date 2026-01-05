"""
Simple system to lock the data while processing.
"""

from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

from api.internal.messaging import log


class Locker:
    """
    Simple class to manage the lock of the system.
    """

    # Default timeout for the lock is 10 minutes.
    lock_timeout = timedelta(minutes=10)
    # Default deadlock is 30 minutes.
    deadlock_timeout = timedelta(minutes=30)

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.lock_file = base_path / "data.lock"

    def is_locked(self):
        if self.lock_file.exists():
            # check age of the file.
            age = datetime.now() - datetime.fromtimestamp(
                self.lock_file.stat().st_mtime
            )
            if age > self.lock_timeout:
                log.warn(
                    f"Depmanager locking: Lock timeout reached try to force lock release."
                )
                self.release_lock()
                return False
            return True
        return False

    def release_lock(self):
        if not self.lock_file.exists():
            log.debug(f"Depmanager locking: Lock already released")
        try:
            self.lock_file.unlink(missing_ok=True)
            if self.lock_file.exists():
                log.debug(f"Depmanager locking: failed Lock released")
            else:
                log.debug(f"Depmanager locking: Lock released")
        except Exception as err:
            log.fatal(f"Depmanager locking: Exception during release: {err}")

    def request_lock(self):
        log.debug(f"Depmanager locking: requesting Lock")
        call_start = datetime.now()
        # wait if there is a lock!
        while self.is_locked():
            sleep(5)
            if datetime.now() - call_start > self.deadlock_timeout:
                log.warn(f"Depmanager locking: Deadlock timeout reached.")
                return False
        # just create the lock file
        if not self.lock_file.parent.exists():
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.lock_file.parent.exists():
                log.fatal(
                    f"Depmanager locking FATAL: Cannot create folder {self.lock_file.parent}, check you permissions."
                )
                exit(1)
        self.lock_file.touch()
        log.debug(f"Depmanager locking: Lock State: {self.lock_file.exists()}")
        # return existence.
        return self.lock_file.exists()
