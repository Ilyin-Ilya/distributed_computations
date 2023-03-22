from threading import Lock
from time import time, time_ns
from typing import Callable, List
from dataclasses import dataclass
from threading import Thread


@dataclass
class Task:
    action: Callable
    delay: float | None = None


class TaskHandler:
    def __init__(self, ):
        self.is_instant_stop = False
        self.task_lock = Lock()
        self.start_lock = Lock()
        self.pause_lock = Lock()
        self.pause_time = None
        self.thread: Thread = Thread(target=self.__start_action__)
        self.is_finished = None
        self.pending_instant_tasks: List[Task] = []
        self.pending_delayed_tasks: List[(Task, float)] = []
        self.scheduled_instant_task: List[Task] = []
        self.scheduled_delayed_tasks = []

    @staticmethod
    def __calculate_delay_time__(delay):
        current_time_seconds = time()
        return delay + current_time_seconds

    def wait(self):
        self.thread.join()

    def schedule_task(self, task: Task) -> bool:
        if not self.is_finished:
            with self.task_lock:
                if task.delay is None or task.delay == 0:
                    self.pending_instant_tasks.append(task)
                else:
                    self.pending_delayed_tasks.append([task, TaskHandler.__calculate_delay_time__(task.delay)])
            return True
        return False

    def start(self):
        with self.start_lock:
            if self.is_finished is None:
                self.is_finished = False
                self.thread.start()

    def pause(self):
        with self.pause_lock:
            if self.pause_time is None:
                self.pause_time = time()

    def unpause(self):
        with self.pause_lock:
            if self.pause_time is not None:
                time_diff = time() - self.pause_time
                with self.task_lock:
                    for i in range(len(self.pending_delayed_tasks)):
                        self.pending_delayed_tasks[i][1] += time_diff
                    for i in range(len(self.scheduled_delayed_tasks)):
                        self.scheduled_delayed_tasks[i][1] += time_diff
                self.pause_time = None

    def __start_action__(self):
        self.__synchronize_with_pending_tasks__()
        while \
                not (not self.scheduled_instant_task and not self.scheduled_delayed_tasks and self.is_finished) \
                        and not self.is_instant_stop:
            if self.pause_time is not None:
                continue
            new_delayed_tasks = []
            current_time = time()

            for task, task_time in self.scheduled_delayed_tasks:
                if task_time <= current_time:
                    task.action()
                else:
                    new_delayed_tasks.append([task, task_time])

            for task in self.scheduled_instant_task:
                task.action()

            self.scheduled_delayed_tasks = new_delayed_tasks
            self.scheduled_instant_task = []
            self.__synchronize_with_pending_tasks__()
        print("Before exit")

    def __synchronize_with_pending_tasks__(self):
        with self.task_lock:
            self.scheduled_instant_task += self.pending_instant_tasks
            self.scheduled_delayed_tasks += self.pending_delayed_tasks
            self.pending_delayed_tasks = []
            self.pending_instant_tasks = []

    def stop(self):
        self.is_finished = True

    def instant_stop(self):
        self.is_instant_stop = True
        self.is_finished = True
