from threading import Lock
from time import time
from typing import Callable


class Task:
    action: Callable
    delay: int


class TaskHandler:
    def __init__(self, thread):
        self.is_instant_stop = False
        self.task_lock = Lock()
        self.start_lock = Lock()
        self.thread = thread
        self.is_finished = None
        self.pending_instant_tasks = []
        self.pending_delayed_tasks = []
        self.scheduled_instant_task = []
        self.scheduled_delayed_task = []

    @staticmethod
    def calculate_delay_time(delay):
        time()
        return None

    def schedule_task(self, task: Task) -> bool:
        if not self.is_finished:
            with self.task_lock:
                if task.delay is None:
                    self.pending_instant_tasks.append(task)
                else:
                    self.pending_delayed_tasks.append((task, TaskHandler.calculate_delay_time(task.delay)))
            return True
        return False

    def start(self):
        with self.start_lock:
            if self.is_finished is None:
                self.is_finished = False
                self.__start_action__()

    def __start_action__(self):
        while \
                (not self.is_finished or self.scheduled_instant_task or self.scheduled_instant_task) \
                        and not self.is_instant_stop:
            new_delayed_tasks = []
            current_time = time()

            for task, task_time in self.scheduled_delayed_task:
                if task_time <= current_time:
                    task.action()
                else:
                    new_delayed_tasks.append((task, task_time))

            for task in self.scheduled_instant_task:
                task.action()

            self.scheduled_delayed_task = new_delayed_tasks
            self.__synchronize_with_pending_tasks__()

    def __synchronize_with_pending_tasks__(self):
        with self.task_lock:
            self.scheduled_instant_task = self.pending_instant_tasks
            self.scheduled_delayed_task += self.pending_delayed_tasks
            self.pending_delayed_tasks = []
            self.pending_instant_tasks = []

    def stop(self):
        self.is_finished = True

    def instant_stop(self):
        self.is_instant_stop = True
        self.is_finished = True
