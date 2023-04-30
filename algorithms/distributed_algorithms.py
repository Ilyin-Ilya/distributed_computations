from distibuted_system import DistributedSystemBuilder
from distributed_objects.process import AbstractProcess
from task_handler.looper import QThreadLooper
from task_handler.taskhandler import TaskHandler
from dataclasses import dataclass
import random
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


@dataclass
class SnapshotMessage:
    counter = 0
    sender = 0
    is_snapshot_taken = False

    def __str__(self) -> str:
        return f"Snapshot message id{self.sender * 100 + self.counter}, snapshot taken {self.is_snapshot_taken}"


@dataclass
class ControlMessage:
    sender = 0
    messages_sent_before_control = 0

    def __str__(self) -> str:
        return f"Control message id{self.sender * 100 + self.counter}, messages sent before: {self.messages_sent_before_control}"


class LaiYangAlgorithmProcess(AbstractProcess):
    def __init__(self, process_id, task_handler: TaskHandler | None, is_init=False, is_initiator=False):
        "sosedi"
        super().__init__(task_handler)
        self.id = process_id
        self.is_init = is_init
        self.is_decided = False
        self.snapshot_taken = False
        self.how_many_messages_send = random.randint(5, 7)
        self.is_initiator = is_initiator
        looper = QThreadLooper(3)
        self.event_task_handler = TaskHandler(looper)
        self.neighbours = dict()
        self.messages_set = dict()
        self.is_first_call = True

    def get_id(self):
        return self.id

    def is_init_process(self):
        return self.is_init

    def is_in_terminal_state(self) -> bool:
        return False

    def get_current_state_information(self):
        return f"Node {self.id} is decided: {self.is_decided}"

    def _on_receive_message_(self, message):
        if self.is_first_call:
            for receiver_id in self.channel_communication_provider.get_available_process_id():
                print(receiver_id)
                self.neighbours[receiver_id] = 0
                self.messages_set[receiver_id] = list()
                self.is_first_call = False

        self.event_task_handler.start()

        if message == AbstractProcess.kick_off_message:
            print("Received kickoff " + str(self.id))
            if not self.is_init:
                raise RuntimeError('kick off message for non initiator')
            counter = 0
            #send random messages to random neighoburs
            for i in range(self.how_many_messages_send):
                new_message = SnapshotMessage()
                new_message.sender = self.id
                new_message.is_snapshot_taken = self.snapshot_taken
                neighbour_id = random.randint(0, max(self.neighbours.keys()))
                while neighbour_id == self.id:
                    neighbour_id = random.randint(0, max(self.neighbours.keys()))
                print(str(self.id) + " + " + str(neighbour_id))

                self.event_task_handler.schedule_action(
                        lambda : self.send_usual_message(neighbour_id, new_message, counter),
                        random.randint(0, 3))

            #send control message
            if self.is_initiator:
                print("INITIATED ")
                self.event_task_handler.schedule_action(
                        lambda: self.take_snapshot(), 2)

        if type(message) == SnapshotMessage:
            if message.is_snapshot_taken:
                self.take_snapshot()
            elif self.snapshot_taken:
                self.messages_set[message.sender].append(message)
                self.check_for_decided()

        print(str(self.id) + "RECEIVED" + str(message))
        if type(message) == ControlMessage:
            print(str(self.id) + "RECEIVED CONTROL MESSAGE")
            self.neighbours[message.sender] = message.messages_sent_before_control
            self.take_snapshot()
            self.check_for_decided()



    def take_snapshot(self):
        print(str(self.id ) + "TAKE SNAPSHOT")
        if not self.snapshot_taken:
            self.snapshot_taken = True
            control_message = ControlMessage()
            for neighbour_id in self.neighbours.keys():
                control_message.counter = self.neighbours[neighbour_id] + 1
                control_message.sender = self.id
                self.send_message(neighbour_id, control_message)


    def send_usual_message(self, receiver_id, message, counter):
        print("sending message from " + str(self.id) + " to " + str(receiver_id))
        message.counter = counter
        self.send_message(receiver_id, message)
        counter += 1
        if not self.snapshot_taken:
            print(str(self.neighbours) + " : " + str(receiver_id))
            self.neighbours[receiver_id] += 1

    def check_for_decided(self):
        for neighbour_id in self.neighbours.keys():
            if len(self.messages_set[neighbour_id]) == self.neighbours[neighbour_id]:
                self.is_decided = True
                self.event_task_handler.stop()
                print("STOPPED")
