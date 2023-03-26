import random

from taskhandler import TaskHandler, Task
from threading import Lock


class AbstractChannel:
    def __init__(self):
        self.handler_lock = Lock()
        self.task_handler = TaskHandler("Channel")

    def perform_message_delivery_actions(self, send_message_callback, message):
        pass

    def start(self):
        pass

    def __debug_wait__(self):
        if self.task_handler is not None:
            self.task_handler.wait()

    """
    Should call stop when want to properly stop channel 
    """

    def stop(self, is_instant=False):
        if self.task_handler is not None:
            if is_instant:
                self.task_handler.instant_stop()
            else:
                self.task_handler.stop()

    def pause(self):
        if self.task_handler is not None:
            self.task_handler.pause()

    def unpause(self):
        if self.task_handler is not None:
            self.task_handler.unpause()


class SimpleDelayChannel(AbstractChannel):
    def __init__(self, delay_range):
        super().__init__()
        self.delay_range = delay_range

    def perform_message_delivery_actions(self, send_message_callback, message):
        self.start()

        message_delivery_task = Task(
            lambda: send_message_callback(message),
            random.randint(self.delay_range[0], self.delay_range[1])
        )
        self.task_handler.schedule_task(message_delivery_task)

    def start(self):
        with self.handler_lock:
            if self.task_handler is None:
                self.task_handler = TaskHandler()
            self.task_handler.start()


class ChannelWrapper(AbstractChannel):
    def __init__(self, channel: AbstractChannel, sender_id=None, receiver_id=None):
        self.inner_channel = channel
        self.sender_id = sender_id
        self.receiver_id = receiver_id

    def get_sender_id(self):
        return self.sender_id

    def get_receiver_id(self):
        return self.receiver_id

    def set_sender_id(self, sender_id):
        self.sender_id = sender_id

    def set_receiver_id(self, receiver_id):
        self.receiver_id = receiver_id

    def perform_message_delivery_actions(self, send_message_callback, message):
        self.inner_channel.perform_message_delivery_actions(send_message_callback, message)

    def start(self):
        self.inner_channel.start()

    def __debug_wait__(self):
        self.inner_channel.__debug_wait__()

    def stop(self, is_instant=False):
        self.inner_channel.stop(is_instant)

    def pause(self):
        self.inner_channel.pause()

    def unpause(self):
        self.inner_channel.unpause()
