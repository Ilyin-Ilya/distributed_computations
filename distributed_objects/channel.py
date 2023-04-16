import random

from task_handler.taskhandler import TaskHandler, Task
from multiprocessing import Lock
from typing import final


class AbstractChannel:
    def __init__(self, task_handler: TaskHandler):
        self.handler_lock = Lock()
        self.task_handler = task_handler

    def set_task_handler(self, task_handler: TaskHandler | None):
        self.task_handler = task_handler

    def deliver_message(self, send_message_callback, message):
        pass

    def start(self):
        with self.handler_lock:
            self.task_handler.start()

    def disable(self):
        pass

    def enable(self):
        pass

    def get_current_state_information(self):
        return "No state information"

    @final
    def __debug_wait__(self):
        if self.task_handler is not None:
            self.task_handler.wait()

    """
    Should call stop when want to properly stop channel 
    """

    @final
    def stop(self, is_instant=False):
        if self.task_handler is not None:
            if is_instant:
                self.task_handler.instant_stop()
            else:
                self.task_handler.stop()

    @final
    def pause(self):
        if self.task_handler is not None:
            self.task_handler.pause()

    @final
    def unpause(self):
        if self.task_handler is not None:
            self.task_handler.unpause()


class SimpleDelayChannel(AbstractChannel):
    def __init__(self, delay_range, task_handler: TaskHandler | None):
        super().__init__(task_handler)
        self.delay_range = delay_range
        self.is_enabled = True
        self.is_enabled_lock = Lock()

    def disable(self):
        with self.is_enabled_lock:
            self.is_enabled = False

    def enable(self):
        with self.is_enabled_lock:
            self.is_enabled = True

    def deliver_message(self, send_message_callback, message):
        if not self.is_enabled:
            return

        self.start()
        random_value = random.random()
        random_delay = self.delay_range[0] + (self.delay_range[1] - self.delay_range[0]) * random_value
        message_delivery_task = Task(
            lambda: send_message_callback(message),
            random_delay
        )
        self.task_handler.schedule_task(message_delivery_task)


class ChannelWrapper(AbstractChannel):
    def __init__(self, channel: AbstractChannel, sender_id=None, receiver_id=None):
        self.inner_channel = channel
        self.sender_id = sender_id
        self.receiver_id = receiver_id

    def set_task_handler(self, task_handler: TaskHandler | None):
        self.inner_channel.set_task_handler(task_handler)

    def get_sender_id(self):
        return self.sender_id

    def get_receiver_id(self):
        return self.receiver_id

    def set_sender_id(self, sender_id):
        self.sender_id = sender_id

    def set_receiver_id(self, receiver_id):
        self.receiver_id = receiver_id

    def deliver_message(self, send_message_callback, message):
        self.inner_channel.deliver_message(send_message_callback, message)

    def start(self):
        self.inner_channel.start()

    def get_current_state_information(self):
        return self.inner_channel.get_current_state_information()

    def __debug_wait__(self):
        self.inner_channel.__debug_wait__()

    def stop(self, is_instant=False):
        self.inner_channel.stop(is_instant)

    def pause(self):
        self.inner_channel.pause()

    def unpause(self):
        self.inner_channel.unpause()

    def disable(self):
        self.inner_channel.disable()

    def enable(self):
        self.inner_channel.enable()
