from time import time
from typing import Callable, List
from dataclasses import dataclass
from multiprocessing import Process, Lock


@dataclass
class Task:
    action: Callable
    delay: float | None = None


class TaskInfo:
    def deschedule_task(self):
        pass

    def is_scheduled(self) -> bool:
        pass

    def is_done(self) -> bool:
        pass

    def time_left(self) -> float:
        pass

    def time_left_relative(self) -> float:
        pass

    def get_delay(self) -> float:
        pass


class TaskHandler:
    def __init__(self, name=""):
        self.name = name
        self.is_instant_stop = False
        self.task_lock = Lock()
        self.start_lock = Lock()
        self.pause_lock = Lock()
        self.pause_time = None
        self.thread: Process = Process(target=self.__start_action__)

        self.is_finished = None
        self.pending_instant_tasks: List[TaskHandler.TaskInfoImpl] = []
        self.pending_delayed_tasks: List[TaskHandler.TaskInfoImpl] = []
        self.scheduled_instant_task: List[TaskHandler.TaskInfoImpl] = []
        self.scheduled_delayed_tasks: List[TaskHandler.TaskInfoImpl] = []

    @staticmethod
    def __calculate_delay_end_time__(delay):
        if delay is None:
            return None
        current_time_seconds = time()
        return delay + current_time_seconds

    def wait(self):
        self.thread.join()

    def schedule_action(self, action: Callable, delay: float = None) -> TaskInfo:
        task = Task(
            action,
            delay
        )
        return self.schedule_task(task)

    def __has_scheduled_or_pending_tasks__(self) -> bool:
        return not (not self.scheduled_instant_task and
                    not self.scheduled_delayed_tasks and
                    not self.pending_instant_tasks and
                    not self.pending_delayed_tasks)

    def schedule_task(self, task: Task) -> TaskInfo:
        task_info = TaskHandler.TaskInfoImpl(self, task)
        if not self.is_finished:
            with self.task_lock:
                if task.delay is None or task.delay == 0:
                    self.pending_instant_tasks.append(task_info)
                else:
                    self.pending_delayed_tasks.append(task_info)
        return task_info

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
                    for pending_task in self.pending_delayed_tasks:
                        pending_task.__set_delay_end_time__(pending_task.__get_delay_end_time__() + time_diff)
                    for scheduled_task in self.scheduled_delayed_tasks:
                        scheduled_task.__set_delay_end_time__(scheduled_task.__get_delay_end_time__() + time_diff)
                self.pause_time = None

    def __start_action__(self):
        self.__synchronize_with_pending_tasks__()
        while (self.__has_scheduled_or_pending_tasks__() or not self.is_finished) \
                and not self.is_instant_stop:
            if self.pause_time is not None:
                continue
            new_delayed_tasks = []
            current_time = time()

            for task_info in self.scheduled_delayed_tasks:
                if not task_info.is_scheduled():
                    continue

                if task_info.__get_delay_end_time__() <= current_time:
                    task_info.__perform_action__()
                else:
                    new_delayed_tasks.append(task_info)

            for task_info in self.scheduled_instant_task:
                if task_info.is_scheduled():
                    task_info.__perform_action__()

            self.scheduled_delayed_tasks = new_delayed_tasks
            self.scheduled_instant_task = []
            self.__synchronize_with_pending_tasks__()

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

    class TaskInfoImpl(TaskInfo):
        def __init__(self, task_handler, task: Task):
            self.__inner_task__ = task
            self.__task_handler__ = task_handler
            self.__delay_end_time__: float | None = TaskHandler.__calculate_delay_end_time__(task.delay)
            self.__update_time_lock__ = Lock()
            self.total_delay: float | None = task.delay
            self.__is_done__: bool = False
            self.__descheduled__: bool = False

        def __get_delay_end_time__(self) -> float:
            return 0 if self.__delay_end_time__ is None else self.__delay_end_time__

        def __set_delay_end_time__(self, new_delay_end_time: float):
            with self.__update_time_lock__:
                self.__delay_end_time__ = new_delay_end_time

        def __perform_action__(self):
            if self.is_scheduled() and not self.is_done():
                self.__mark_as_done__()
                self.__inner_task__.action()
                self.deschedule_task()

        def deschedule_task(self):
            self.__descheduled__ = True

        def is_scheduled(self) -> bool:
            return not self.__descheduled__

        def is_done(self) -> bool:
            return self.__is_done__

        def __mark_as_done__(self):
            self.__is_done__ = True

        def get_delay(self) -> float:
            return 0 if self.total_delay is None or self.total_delay < 0 else self.total_delay

        def time_left(self) -> float:
            if not self.is_scheduled() or self.is_done():
                return -1

            if self.get_delay() == 0:
                return 0

            pause_time = self.__task_handler__.pause_time

            if pause_time:
                time_left = self.__delay_end_time__ - pause_time
                if time_left >= 0:
                    return time_left
                else:
                    return 0

        def time_left_relative(self) -> float:
            time_left = self.time_left()
            if self.get_delay() == 0 or time_left == -1:
                return 0

            if self.get_delay() > time_left:
                return time_left / self.get_delay()
            else:
                return 1
