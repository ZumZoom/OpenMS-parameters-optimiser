import time


class Timer:
    def __init__(self):
        self.begin = None

    def start(self):
        self.begin = time.time()

    def get(self):
        return time.time() - self.begin