from distibuted_system import DistributedSystemBuilder, InternalAction
from distributed_objects.process import AbstractProcess
from task_handler.looper import QThreadLooper, ProcessLooper
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
    counter = 0
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
        self.how_many_messages_send = random.randint(3, 5)
        self.is_initiator = is_initiator
        looper = ProcessLooper(5)
        self.event_task_handler = TaskHandler(looper)
        self.neighbours = dict()
        self.sent_messages = dict()
        self.collected_snapshots = dict()
        self.messages_set = dict()
        self.is_first_call = True
        self.event_task_handler.start()
        self.counter = 0

    def get_id(self):
        return self.id

    def is_init_process(self):
        return self.is_init

    def is_in_terminal_state(self) -> bool:
        return False

    def get_current_state_information(self):
        return f"Node {self.id} is decided: {self.is_decided}"

    def _on_receive_message_(self, message):
        if type(message) == InternalAction:
            return

        if message != AbstractProcess.kick_off_message:
            print("Node " + str(self.id) + " received from " + str(message.sender) + " " + str(message))


        if self.is_first_call:
            for receiver_id in self.channel_communication_provider.get_available_process_id():
                print(receiver_id)
                self.neighbours[receiver_id] = 0
                self.sent_messages[receiver_id] = 0
                self.messages_set[receiver_id] = list()
                self.collected_snapshots[receiver_id] = False
                self.is_first_call = False

        if message == AbstractProcess.kick_off_message:
            if not self.is_init:
                raise RuntimeError('kick off message for non initiator')
            #send random messages to random neighoburs
            for i in range(self.how_many_messages_send):
                self.event_task_handler.schedule_action(
                        lambda : self.send_usual_message(),
                        random.randint(0, 20))

            #send control message
            if self.is_initiator:
                self.event_task_handler.schedule_action(
                        lambda: self.take_snapshot(), 5)

        if type(message) == SnapshotMessage:
            #print(str(message.sender) + " : " + str(self.id) + " + " +str(self.collected_snapshots))
            if message.is_snapshot_taken:
                self.collected_snapshots[message.sender] = True
                self.take_snapshot()
            else:
                self.messages_set[message.sender].append(message)
                self.check_for_decided()

        if type(message) == ControlMessage:
            self.neighbours[message.sender] = message.messages_sent_before_control
            self.collected_snapshots[message.sender] = True
            self.take_snapshot()
            self.check_for_decided()



    def take_snapshot(self):
        if not self.snapshot_taken:
            self.snapshot_taken = True
            print(self.neighbours)
            for neighbour_id in self.neighbours.keys():
                control_message = ControlMessage()
                control_message.messages_sent_before_control = self.sent_messages[neighbour_id] + 1
                control_message.sender = self.id
                control_message.counter = self.counter
                self.counter+=1
                print("Node " + str(self.id) + " send to " + str(neighbour_id) + " " + str(control_message))
                self.send_message(neighbour_id, control_message)


    def send_usual_message(self):
        new_message = SnapshotMessage()
        new_message.sender = self.id
        neighbour_id = random.randint(0, max(self.neighbours.keys()))
        while neighbour_id == self.id:
            neighbour_id = random.randint(0, max(self.neighbours.keys()))
        print(str(self.id) + " + " + str(neighbour_id))

        new_message.counter = self.counter
        self.counter += 1
        new_message.is_snapshot_taken = self.snapshot_taken
        print("Node " + str(self.id) + " send to " + str(neighbour_id) + " " + str(new_message))
        self.send_message(neighbour_id, new_message)
        print(self.collected_snapshots)
        if not self.collected_snapshots[neighbour_id]:
            self.sent_messages[neighbour_id] += 1

    def check_for_decided(self):
        print(str(self.id) + str(self.messages_set) + str(self.neighbours))
        is_decided = True
        for neighbour_id in self.neighbours.keys():
            if not (len(self.messages_set[neighbour_id]) + 1 == self.neighbours[neighbour_id] \
                    and self.collected_snapshots[neighbour_id]):
                    is_decided = False
        if is_decided:
            if not self.is_decided:
                message = InternalAction()
                message.action = "Node " + str(self.id) + " has been terminated"
                print("Node " + str(self.id) + " has been terminated")
                self.send_message(self.id, message)
                self.is_decided = True
                print(self.is_decided)
                self.event_task_handler.stop()
                print("STOPPED")
