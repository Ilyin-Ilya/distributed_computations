from distributed_objects.process import AbstractProcess
from task_handler.taskhandler import TaskHandler
from dataclasses import dataclass
from typing import Set


@dataclass
class EchoMessage:
    counter = 0
    sender = 0

    def __str__(self) -> str:
        return f"Echo message id{self.sender * 100 + self.counter}"


class EchoAlgorithmProcess(AbstractProcess):
    def __init__(self, process_id, task_handler: TaskHandler | None, is_init=False):
        super().__init__(task_handler)
        self.id = process_id
        self.is_init = is_init
        self.is_decided = False
        self.parent = None
        self.received_from = set()

    def get_id(self):
        return self.id

    def is_init_process(self):
        return self.is_init

    def is_in_terminal_state(self) -> bool:
        return False

    def get_current_state_information(self):
        return f"Node {self.id} is decided: {self.is_decided}"

    def _on_receive_message_(self, message: EchoMessage):
        if self.is_decided:
            return
        is_first_message = message == AbstractProcess.kick_off_message or (self.parent is None and not self.is_init)

        if message == AbstractProcess.kick_off_message:
            if not self.is_init:
                raise RuntimeError('kick off message for non initiator')
            new_message = EchoMessage()
            new_message.counter = 0
            new_message.sender = self.id
        else:
            self.received_from.add(message.sender)
            new_message = EchoMessage()
            new_message.counter = message.counter + 1
            new_message.sender = self.id

        if not self.is_init and self.parent is None:
            self.parent = message.sender

        if is_first_message:
            self.send_to_all_neighbours(new_message)

        self.is_decided = True
        for receiver_id in self.channel_communication_provider.get_available_process_id():
            if receiver_id != self.id and receiver_id not in self.received_from:
                self.is_decided = False
                break

        if self.is_decided and not self.is_init:
            self.channel_communication_provider.send_message(self.parent, new_message)

    def send_to_all_neighbours(self, new_message):
        for receiver_id in self.channel_communication_provider.get_available_process_id():
            if receiver_id != self.parent:
                self.channel_communication_provider.send_message(receiver_id, new_message)
