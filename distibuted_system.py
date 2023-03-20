from taskhandler import TaskHandler
from threading import main_thread
from channel import AbstractChannel, SimpleDelayChannel
from typing import Set, Dict
from abstract_proccess import ChannelCommunicationProvider, AbstractProcess, SimpleProcess


class DistributedSystem:
    empty_entry = "EmptyEntry"

    def __init__(self):
        self.main_task_handler = TaskHandler(main_thread())  # receive messages from channels
        self.communication_dict: Dict = {}
        self.process_dictionary: Dict = {}
        self.init_process: Dict = {}

    def stop_and_get_snapshot(self):
        pass

    def set_channel(self, sender_id, receiver_id, channel: AbstractChannel):
        self.communication_dict[(sender_id, receiver_id)] = channel

    def set_process(self, process: AbstractProcess) -> bool:
        if process.is_init_process():
            self.init_process[process.get_id()] = process
        else:
            self.process_dictionary[process.get_id()] = process
        process.set_channel_communication_provider("TODO")  # TODO

    def set_communication_dict(self, dict: Dict):
        for item in dict.items():
            self.communication_dict = DistributedSystem.empty_entry

    def set_communication_graph(self, graph):
        pass


class DistributedSystemBuilder:
    def build(self) -> DistributedSystem:
        pass
