class Event:
    pass


class Observer:
    def handle(self, observable, event: Event):
        pass


class Observable:
    def __init__(self):
        self.observers = set()
        self.valid = True

    def subscribe(self, observer: Observer):
        self.observers.add(observer)

    def un_subscribe(self, observer: Observer):
        self.observers.remove(observer)

    def notify(self, event):
        self.valid = False
        for observer in self.observers:
            observer.handle(self, event)

