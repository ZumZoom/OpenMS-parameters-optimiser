__author__ = 'zumzoom'


class Singleton:
    def __init__(self, decorated):
        self._decorated = decorated
        self._instance = None

    def instance(self):
        if self._instance is not None:
            return self._instance
        else:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)