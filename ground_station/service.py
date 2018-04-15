import logging
from logging import getLogger
from queue import Empty
from sched import scheduler
from time import sleep, time
from threading import Event, Thread


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
        self.log = getLogger(str(name) + self.__class__.__name__)

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
        self.thread = None
        self.stop_flag = None
        self.scheduler_event = scheduler_event


class ServiceManager(object):
    """Manages services"""
    def __init__(self, services):
        """UplinkServiceHandler

        :param list services: list of Service objects
        """
        self.log = getLogger(self.__class__.__name__)

        self._scheduler = scheduler(time, sleep)
        self._services = dict()

        for service in services:
            self._services[service.name] = SchedulerService(service, False, None)

        # self._scheduler.run()

    def _periodic(self, name, action, args=()):
        """Start a periodic event

        :param str name: name of service
        :param callable action: action to call at service frequency
        :param args: arguments to pass to action
        """
        if self._services[name].stop_flag.is_set():
            self.log.debug('Service {name} done'.format(**locals()))
            self._services[name].running = False
            self._services[name].thread = None
            self._services[name].stop_flag = None
            self._services[name].scheduler_event = None
            return

        service = self._services[name].service
        self._services[name].scheduler_event = \
            self._scheduler.enter(service.interval, service.priority, self._periodic, (name, service.step, args))
        self.log.debug('Running service step {name}'.format(**locals()))
        action(*args)

    def start_all(self):
        """Start all services"""
        for service in self._services:
            self.start(service.service.name)

    def start(self, name):
        """Start service

        :param str name: name of service to start
        """
        if name not in self._services:
            self.log.warning('Service {name} does not exist'.format(**locals()))
            return

        scheduler_service = self._services[name]
        service = scheduler_service.service

        if not scheduler_service.running:
            self.log.info('Starting service {name}'.format(**locals()))

            scheduler_service.stop_flag = Event()
            self._periodic(name, service.step)
            scheduler_service.thread = Thread(name='{name}Service'.format(**locals()), target=self._scheduler.run)
            # scheduler_service.thread = Thread(target=self._periodic, args=(name, service.step))
            scheduler_service.thread.start()

            scheduler_service.running = True

            # self._scheduler.run()
        else:
            self.log.debug('Service {name} is already running'.format(**locals()))

    def stop(self, name):
        """Stop service

        :param str name: name of service to stop
        """
        if name not in self._services:
            self.log.warning('Service {name} does not exist'.format(**locals()))
            return

        scheduler_service = self._services[name]

        # if the service exists and is running
        if self._services[name].running:
            self.log.info('Stopping service {name}'.format(**locals()))
            scheduler_service.stop_flag.set()

            # scheduler_service.thread.join()

            # scheduler_service.thread = None

        else:
            self.log.debug('Service {name} is not running'.format(**locals()))


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
    print('here')

    sleep(5)
    ush.stop('Uplink')
    print('done')


if __name__ == '__main__':
    test()
