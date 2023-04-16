from multiprocessing import Process, Lock as PLock, Value as PValue
from threading import Thread, Lock
from time import sleep


class Looper:
    def __init__(self, loop_action, loop_delay_ms):
        self.loop_delay_ms = loop_delay_ms
        self.loop_action = loop_action

    def set_loop_action(self, loop_action):
        self.loop_action = loop_action

    def exit_loop(self):
        pass

    def do_loop(self):
        pass

    def pause(self):
        pass

    def unpause(self):
        pass

    def wait(self):
        pass


class ThreadLooper(Looper):
    def __init__(self, loop_action, loop_delay_ms: int | None = None):
        super().__init__(loop_action, loop_delay_ms)
        self.lock = Lock()
        self.is_finished = None
        self.is_paused = None
        self.thread = Thread(target=self.__loop__)

    def exit_loop(self):
        with self.lock:
            self.is_finished = True

    def __loop__(self):
        while not self.is_finished:
            if not self.is_paused:
                self.loop_action()
            if self.loop_delay_ms is not None:
                sleep(self.loop_delay_ms // 1000)

    def do_loop(self):
        with self.lock:
            if self.is_finished is None:
                self.is_finished = False
                self.thread.start()

    def pause(self):
        with self.lock:
            self.is_paused = True

    def unpause(self):
        with self.lock:
            self.is_paused = False

    def wait(self):
        self.thread.join()


class ProcessLooper(Looper):
    def __init__(self, loop_action, loop_delay_ms: int | None = None):
        super().__init__(loop_action, loop_delay_ms)
        self.is_finished = PValue('i', -1)
        self.is_paused = PValue('i', 0)
        self.process = Process(target=self.do_loop())

    def __loop__(self):
        pass

    def exit_loop(self):
        pass

    def do_loop(self):
        pass

    def pause(self):
        pass

    def unpause(self):
        pass

    def wait(self):
        self.process.join()


from PyQt5.QtCore import QThread


class QThreadLooper(Looper):
    class WorkerThread(QThread):
        def __init__(self, looper):
            super().__init__()
            self.looper = looper

        def run(self):
            while not self.looper.is_finished:
                if not self.looper.is_paused:
                    self.looper.loop_action()
                if self.looper.loop_delay_ms is not None:
                    self.msleep(self.looper.loop_delay_ms)

    def __init__(self, loop_action, loop_delay_ms: int | None = None):
        super().__init__(loop_action, loop_delay_ms)
        self.lock = Lock()
        self.is_finished = None
        self.is_paused = None
        self.thread = QThreadLooper.WorkerThread(self)

    def exit_loop(self):
        with self.lock:
            self.is_finished = True

    def do_loop(self):
        with self.lock:
            if self.is_finished is None:
                self.is_finished = False
                self.thread.start()

    def pause(self):
        with self.lock:
            self.is_paused = True

    def unpause(self):
        with self.lock:
            self.is_paused = False

    def wait(self):
        self.thread.join()
