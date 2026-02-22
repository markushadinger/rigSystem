class Signal:
    def __init__(self):
        self._subscribers = []

    def connect(self, func):
        self._subscribers.append(func)

    def emit(self, *args, **kwargs):
        for func in self._subscribers:
            func(*args, **kwargs)
