from taskhandler import TaskHandler
from threading import main_thread
from channel import AbstractChannel


class DistributedSystem:
    def __init__(self):
        self.main_task_handler = TaskHandler(main_thread())  # receive messages from channels

    def create_channel(self, sender_id, receiver_id, channel: AbstractChannel):
        pass

    def create_process(self,):
        pass