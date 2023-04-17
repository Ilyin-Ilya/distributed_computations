from typing import Callable
from task_handler.task_scheduler import TaskScheduler, Task, TaskInfo, TimingTaskScheduler
from task_handler.looper import Looper


class TaskHandler:
    def __init__(self, looper: Looper, task_scheduler: TaskScheduler = TimingTaskScheduler(), name=""):
        self.name = name
        self.task_scheduler = task_scheduler
        self.looper: Looper = looper
        self.looper.set_loop_action(self.__loop_action__)
        self.is_instant_stop = False
        self.is_finished = None

    def wait(self):
        self.looper.wait()

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
        if self.is_finished is None:
            self.is_finished = False
            self.looper.do_loop()

    def pause(self):
        self.task_scheduler.stop()

    def unpause(self):
        self.task_scheduler.start()

    def __loop_action__(self):
        if (self.task_scheduler.has_task_to_do() or not self.is_finished) \
                and not self.is_instant_stop:
            self.task_scheduler.do_tasks()
        else:
            self.looper.exit_loop()

    def stop(self):
        self.is_finished = True

    def instant_stop(self):
        self.is_instant_stop = True
        self.is_finished = True
