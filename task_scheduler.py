from typing import Callable, List
from dataclasses import dataclass
from multiprocessing import Lock as PLock
from time import time
from typing import final
import heapq


@dataclass
class Task:
    action: Callable
    delay: float | None = None


class TaskInfo:
    def __init__(self):
        self.__is_done__: bool = False
        self.__descheduled__: bool = False

    @final
    def deschedule_task(self):
        self.__descheduled__ = True

    @final
    def is_scheduled(self) -> bool:
        return not self.__descheduled__

    @final
    def is_done(self) -> bool:
        return self.__is_done__

    @final
    def time_left_relative(self) -> float:
        time_left = self.time_left()
        if self.get_delay() == 0 or time_left == -1:
            return 0

        if self.get_delay() > time_left:
            return time_left / self.get_delay()
        else:
            return 1

    def time_left(self) -> float:
        pass

    def get_delay(self) -> float:
        pass


class TaskScheduler:
    def schedule_task(self, task: Task) -> TaskInfo:
        pass

    def do_tasks(self):
        pass

    def has_task_to_do(self) -> bool:
        pass

    def start(self):
        pass

    def stop(self):
        pass


class TimingTaskScheduler(TaskScheduler):
    @staticmethod
    def __calculate_delay_end_time__(delay):
        if delay is None:
            return None
        current_time_seconds = time()
        return delay + current_time_seconds

    class TimingTaskInfo(TaskInfo):
        def __init__(self, scheduler, task: Task):
            super().__init__()
            self.scheduler = scheduler
            self.__inner_task__ = task
            self.__delay_end_time__: float | None = TimingTaskScheduler.__calculate_delay_end_time__(task.delay)
            self.__update_time_lock__ = PLock()
            self.total_delay: float | None = task.delay

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

        def __mark_as_done__(self):
            self.__is_done__ = True

        def get_delay(self) -> float:
            return 0 if self.total_delay is None or self.total_delay < 0 else self.total_delay

        def time_left(self) -> float:
            if not self.is_scheduled() or self.is_done():
                return -1

            if self.get_delay() == 0:
                return 0

            pause_time = self.scheduler.pause_time

            if pause_time:
                time_left = self.__delay_end_time__ - pause_time
                if time_left >= 0:
                    return time_left
                else:
                    return 0

    def __init__(self):
        self.task_lock = PLock()
        self.pause_lock = PLock()
        self.pause_time = None
        self.pending_instant_tasks: List[TimingTaskScheduler.TimingTaskInfo] = []
        self.pending_delayed_tasks: List[TimingTaskScheduler.TimingTaskInfo] = []
        self.scheduled_instant_task: List[TimingTaskScheduler.TimingTaskInfo] = []
        self.scheduled_delayed_tasks: List[TimingTaskScheduler.TimingTaskInfo] = []

    def schedule_task(self, task: Task) -> TaskInfo:
        task_info = TimingTaskScheduler.TimingTaskInfo(self, task)

        with self.task_lock:
            if task.delay is None or task.delay == 0:
                self.pending_instant_tasks.append(task_info)
            else:
                self.pending_delayed_tasks.append(task_info)
        return task_info

    def do_tasks(self):
        if self.pause_time is not None:
            return
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

    def has_task_to_do(self) -> bool:
        return not (not self.scheduled_instant_task and
                    not self.scheduled_delayed_tasks and
                    not self.pending_instant_tasks and
                    not self.pending_delayed_tasks)

    def start(self):
        with self.pause_lock:
            if self.pause_time is not None:
                time_diff = time() - self.pause_time
                with self.task_lock:
                    for pending_task in self.pending_delayed_tasks:
                        pending_task.__set_delay_end_time__(pending_task.__get_delay_end_time__() + time_diff)
                    for scheduled_task in self.scheduled_delayed_tasks:
                        scheduled_task.__set_delay_end_time__(scheduled_task.__get_delay_end_time__() + time_diff)
                self.pause_time = None

    def stop(self):
        with self.pause_lock:
            if self.pause_time is None:
                self.pause_time = time()


class InstantTaskScheduler(TaskScheduler):
    class InstantTaskInfo(TaskInfo):
        def __init__(self, scheduler, task: Task):
            super().__init__()
            self.scheduler = scheduler
            self.__inner_task__ = task
            self.time_multiplier = 1000
            self.__delay_end_time__: int
            if task.delay is None:
                self.__delay_end_time__ = self.scheduler.local_clocks
            else:
                self.__delay_end_time__ = self.scheduler.local_clocks + int(task.delay * 10 * self.time_multiplier)

        def __perform_action__(self):
            if self.is_scheduled() and not self.is_done():
                self.__mark_as_done__()
                self.__inner_task__.action()
                self.deschedule_task()

        def __mark_as_done__(self):
            self.__is_done__ = True

        def get_delay(self) -> float:
            delay = self.__inner_task__.delay
            return 0 if delay is None or delay < 0 else delay

        def time_left(self) -> float:
            if not self.is_scheduled() or self.is_done():
                return -1

            time_left = (self.__delay_end_time__ - self.scheduler.local_clocks) / self.time_multiplier
            return 0 if time_left < 0 else time_left

        def __lt__(self, other):
            return self.__delay_end_time__ < other.__delay_end_time__

    def __init__(self):
        self.task_lock = PLock()
        self.task_heap: List[InstantTaskScheduler.InstantTaskInfo] = []
        self.pending_tasks_heap: List[InstantTaskScheduler.InstantTaskInfo] = []
        self.local_clocks: int = 1

    def schedule_task(self, task: Task) -> TaskInfo:
        task_info = InstantTaskScheduler.InstantTaskInfo(self, task)
        with self.task_lock:
            heapq.heappush(self.task_heap, task_info)
        return task_info

    def do_tasks(self):
        self.__synchronize_pending_tasks__()
        task_info = None if not self.task_heap  else heapq.heappop(self.task_heap)

        if task_info and task_info.is_scheduled() and not task_info.is_done():
            if self.local_clocks <= task_info.__delay_end_time__:
                self.local_clocks = task_info.__delay_end_time__
            task_info.__perform_action__()

    def __synchronize_pending_tasks__(self):
        with self.task_lock:
            self.task_heap = list(heapq.merge(self.task_heap, self.pending_tasks_heap))
            self.pending_tasks_heap = []

    def has_task_to_do(self) -> bool:
        return not (not self.pending_tasks_heap and not self.task_heap)
