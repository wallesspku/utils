import os
import logging

from .abs_setup import AbstractSetup

logger = logging.getLogger('walless')


class LoggerSetup(AbstractSetup):
    def __init__(self):
        super().__init__()
        self.name = 'logger'
        self.log_level = 0
        self._formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

    def setup(self, log_paths=None, formatter=None):
        self.setup_logger(formatter)
        if log_paths:
            for log_path in log_paths:
                self.add_file_handler(log_path, formatter)

    def setup_logger(self, formatter=None):
        if formatter is None:
            formatter = self._formatter
        if os.environ.get('DEBUG', '0') == '1':
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.WARNING)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    def add_file_handler(self, file_path: str, formatter=None):
        if formatter is None:
            formatter = self._formatter
        file_path = os.path.expanduser(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def add_notifier(self):
        try:
            from notifier import NotifierHandler
            logger.addHandler(NotifierHandler())
        except:
            pass


logger_setup = LoggerSetup()
