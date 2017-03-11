class Observer:
    def notify(self, invalid):
        pass


class Observable:
    def __init__(self):
        self.observers = set()
        self.valid = True

    def subscribe(self, observer: Observer):
        self.observers.add(observer)

    def un_subscribe(self, observer: Observer):
        self.observers.remove(observer)

    def invalidate(self):
        self.valid = False
        for observer in self.observers:
            observer.notify(self)
