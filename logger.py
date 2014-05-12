import logging
from singleton import Singleton

__author__ = 'zumzoom'


@Singleton
class Logger():
    def __init__(self):
        self.logger = logging.getLogger('logger')
        handler = logging.FileHandler('log.txt')
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log(self, what):
        self.logger.info(what)


def log(what):
    Logger.instance().log(what)
