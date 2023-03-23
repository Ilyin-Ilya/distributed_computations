from dataclasses import dataclass
from typing import final, List
from distibuted_system import DistributedSystem


class ChannelCommunicationProvider:
    def get_available_process_id(self) -> List: pass

    def send_message(self, receiver_id, message) -> None: pass


class AbstractProcess:
    def __init__(self):
        self.channel_communication_provider: ChannelCommunicationProvider = None

    def set_channel_communication_provider(self, channel_communication_provider: ChannelCommunicationProvider):
        self.channel_communication_provider = channel_communication_provider

    def get_id(self):
        pass

    def is_init_process(self):
        return False

    def is_in_terminal_state(self) -> bool:
        pass

    def on_receive_message(self, message) -> None:
        pass

    @final
    def send_message(self, receiver_id, message):
        self \
            .channel_communication_provider \
            .send_message(receiver_id, message)

    @final
    def get_available_channels(self) -> List:
        return self.channel_communication_provider.get_available_process_id()


class SimpleProcess(AbstractProcess):
    def __init__(self, id):
        super().__init__()
        self.id = id

    def get_id(self):
        return self.id

    def is_init_process(self):
        return False

    def is_in_terminal_state(self) -> bool:
        return False

    def on_receive_message(self, message) -> None:
        for receiver_id in self.channel_communication_provider.get_available_process_id():
            self.channel_communication_provider.send_message(receiver_id, message)
