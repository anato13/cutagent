"""Run expensive operations off the interface thread."""
from PySide6.QtCore import QThread, Signal

from .video import Cancelled, Runner


class Job(QThread):
    progress = Signal(float, str)
    result = Signal(object)
    failed = Signal(str)
    cancelled = Signal(str)

    def __init__(self, operation, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.runner = Runner()

    def run(self):
        try:
            value = self.operation(self.runner, self.progress.emit)
            if not (isinstance(value, dict) and value.get('committed') is True):
                self.runner.check()
            self.result.emit(value)
        except Cancelled as error:
            self.cancelled.emit(str(error))
        except Exception as error:
            self.failed.emit(str(error) or type(error).__name__)

    def cancel(self):
        self.runner.cancel()
