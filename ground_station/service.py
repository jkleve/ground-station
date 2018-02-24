import logging
from logging import getLogger
from queue import Empty
from sched import scheduler
from time import sleep, time


class Service(object):
    """Service

    Holds data about a service
    """
    def __init__(self, name, action, events, frequency, priority=1):
        """Service

        :param str name: name of service to keep track of it. Use this when starting and stopping services
        :param callable action: action to call at frequency
        :param events: queue type object that implements a get(block=) method
        :param float frequency: frequency to run service at when it's running
        :param int priority: a higher lower number represents a higher priority
        """
        self.log = getLogger(str(name) + str(self.__class__))

        self.name = name
        self.events = events
        self.interval = 1/frequency
        self.priority = priority
        self._action = action

    def step(self):
        try:
            event = self.events.get(block=False)
        except Empty:
            pass
        else:
            self.log.debug('Emitting event {}'.format(event))
            self._action(event)


class SchedulerService(object):
    """Scheduler Service container to keep track of all service data relevant to scheduler"""
    def __init__(self, service, running, scheduler_event):
        """

        :param Service service: service instance
        :param bool running: boolean of if this service is running
        :param Event scheduler_event: event object returned by scheduler.enter
        """
        self.service = service
        self.running = running
        self.scheduler_event = scheduler_event


class ServiceManager(object):
    """Manages services"""
    def __init__(self, services):
        """UplinkServiceHandler

        :param list services: list of Service objects
        """
        self.log = getLogger(str(self.__class__))

        self._scheduler = scheduler(time, sleep)
        self._services = dict()

        for service in services:
            self._services[service.name] = SchedulerService(service, False, None)

        self._scheduler.run()

    def _periodic(self, name, action, args=()):
        """Start a periodic event

        :param str name: name of service
        :param callable action: action to call at service frequency
        :param args: arguments to pass to action
        """
        service = self._services[name].service
        self._services[name].scheduler_event = \
            self._scheduler.enter(service.interval, service.priority, self._periodic, (name, service.step, args))
        action(*args)

    def start_all(self):
        """Start all services"""
        for service in self._services:
            self.start(service.service.name)

    def start(self, name):
        """Start service

        :param str name: name of service to start
        """
        if name in self._services and not self._services[name].running:
            service = self._services[name].service
            self.log.info('Starting service {}'.format(name))
            self._periodic(name, service.step)
            service.running = True

        self._scheduler.run()

    def stop(self, name):
        """Stop service

        :param str name: name of service to stop
        """
        # if the service exists and is running
        if name in self._services and self._services[name].running:
            try:
                self.log.info('Stopping service {}'.format(name))
                self._scheduler.cancel(self._services[name].event)
            except ValueError:
                self.log.warning('Service {} does not have an event scheduled'.format(name))
            self._services[name].running = False


def test():
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Starting service test')

    class Test(object):
        def __init__(self):
            self.i = 0

        def get(self, block):
            self.i += 1
            return self.i

    class MockConn(object):
        def send(self, datum):
            print(datum)

    t1 = Test()
    s1 = Service('Uplink', MockConn().send, t1, 20)
    ush = ServiceManager([s1, ])
    ush.start('Uplink')


if __name__ == '__main__':
    test()
