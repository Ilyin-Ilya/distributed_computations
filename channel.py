import random

from threading import Thread
from typing import final
from taskhandler import TaskHandler, Task


class AbstractChannel:
    def __init__(self):
        self.send_message_callback = None
        self.task_handler = self.create_task_new_task_handler()

    def perform_message_delivery_actions(self, message):
        pass

    def create_task_new_task_handler(self) -> TaskHandler:
        if self.task_handler is not None:
            self.task_handler.stop()
        return TaskHandler(Thread())

    @final
    def set_send_message_callback(self, send_message_callback):
        self.send_message_callback = send_message_callback

    """
    Send message to distributed system 
    """
    @final
    def send_finally(self, message):
        self.send_message_callback(message)

    """
    Should call stop when want to properly stop channel 
    """
    def stop(self):
        pass


class SimpleDelayChannel(AbstractChannel):
    def __init__(self, delay_range):
        super().__init__()
        self.delay_range = delay_range

    def perform_message_delivery_actions(self, message):
        self.start()

        message_delivery_task = Task(
            lambda: self.send_finally(message),
            random.randint(self.delay_range[0], self.delay_range[1])
        )
        self.task_handler.schedule_task(message_delivery_task)

    def stop(self):
        if self.task_handler is not None:
            self.task_handler.stop()
            self.task_handler = None

    def start(self):
        if self.task_handler is None:
            self.task_handler = self.create_task_new_task_handler()
        self.task_handler.start()
