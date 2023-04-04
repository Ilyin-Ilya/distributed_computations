from typing import final, List
from taskhandler import TaskHandler
from threading import Lock


class ChannelCommunicationProvider:
    def get_available_process_id(self) -> List: pass

    def send_message(self, receiver_id, message) -> None: pass


class AbstractProcess:
    kick_off_message = "Start initially"

    def __init__(self):
        self.channel_communication_provider: ChannelCommunicationProvider | None = None
        self.task_handler = TaskHandler("Channel")
        self.is_enabled = True
        self.is_disabled_lock = Lock()

    def set_channel_communication_provider(self, channel_communication_provider: ChannelCommunicationProvider):
        self.channel_communication_provider = channel_communication_provider

    def get_id(self):
        pass

    def is_init_process(self):
        return False

    def is_in_terminal_state(self) -> bool:
        pass

    def _on_receive_message_(self, message):
        """
        Implement this method with actual algorithm running on the node
        """
        pass

    def get_current_state_information(self):
        return "No state information"

    @final
    def disable(self):
        with self.is_disabled_lock:
            self.is_enabled = False

    @final
    def enable(self):
        with self.is_disabled_lock:
            self.is_enabled = True

    @final
    def receive_message(self, message):
        if self.is_enabled:
            self.task_handler \
                .schedule_action(lambda: self._on_receive_message_(message))

    @final
    def start(self):
        self.task_handler.start()

    @final
    def pause(self):
        self.task_handler.pause()

    @final
    def unpause(self):
        self.task_handler.unpause()

    @final
    def stop(self, is_instant=False):
        if is_instant:
            self.task_handler.instant_stop()
        else:
            self.task_handler.stop()

    @final
    def send_message(self, receiver_id, message):
        self \
            .channel_communication_provider \
            .send_message(receiver_id, message)

    @final
    def __get_available_channels__(self) -> List:
        return self.channel_communication_provider.get_available_process_id()


class SimpleEchoProcess(AbstractProcess):
    def __init__(self, process_id):
        super().__init__()
        self.process_id = process_id

    def get_id(self):
        return self.process_id

    def is_init_process(self):
        return False

    def is_in_terminal_state(self) -> bool:
        return False

    def _on_receive_message_(self, message):
        for receiver_id in self.channel_communication_provider.get_available_process_id():
            self.channel_communication_provider.send_message(receiver_id, message)
