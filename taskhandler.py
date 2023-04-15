from typing import Callable
from multiprocessing import Process, Lock
from task_scheduler import TaskScheduler, Task, TaskInfo, TimingTaskScheduler


class TaskHandler:
    def __init__(self, task_scheduler: TaskScheduler = TimingTaskScheduler(), name=""):
        self.name = name
        self.task_scheduler = task_scheduler
        self.is_instant_stop = False
        self.task_lock = Lock()
        self.start_lock = Lock()
        self.process: Process = Process(target=self.__start_action__)
        self.is_finished = None

    def wait(self):
        self.process.join()

    def schedule_action(self, action: Callable, delay: float = None) -> TaskInfo:
        task = Task(
            action,
            delay
        )
        return self.schedule_task(task)

    def schedule_task(self, task: Task) -> TaskInfo | None:
        if not self.is_finished:
            return self.task_scheduler.schedule_task(task)
        return None

    def start(self):
        with self.start_lock:
            if self.is_finished is None:
                self.is_finished = False
                self.process.start()

    def pause(self):
        self.task_scheduler.stop()

    def unpause(self):
        self.task_scheduler.start()

    def __start_action__(self):
        while (self.task_scheduler.has_task_to_do() or not self.is_finished) \
                and not self.is_instant_stop:
            self.task_scheduler.do_tasks()

    def stop(self):
        self.is_finished = True

    def instant_stop(self):
        self.is_instant_stop = True
        self.is_finished = True
