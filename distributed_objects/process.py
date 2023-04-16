from typing import final, List
from taskhandler import TaskHandler
from threading import Lock


class ChannelCommunicationProvider:
    def get_available_process_id(self) -> List: pass

    def send_message(self, receiver_id, message) -> None: pass


class AbstractProcess:
    kick_off_message = "Start initially"

    def __init__(self, task_handler: TaskHandler | None):
        self.channel_communication_provider: ChannelCommunicationProvider | None = None
        self.task_handler: TaskHandler | None = task_handler  # if no task handler, then processing is synchronous
        self.is_enabled = True
        self.is_disabled_lock = Lock()

    def set_task_handler(self, task_handler: TaskHandler | None):
        self.task_handler = task_handler

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
            if self.task_handler is None:
                self._on_receive_message_(message)
            else:
                self.task_handler \
                    .schedule_action(lambda: self._on_receive_message_(message))

    @final
    def start(self):
        if self.task_handler is not None:
            self.task_handler.start()

    @final
    def pause(self):
        if self.task_handler is not None:
            self.task_handler.pause()

    @final
    def unpause(self):
        if self.task_handler is not None:
            self.task_handler.unpause()

    @final
    def stop(self, is_instant=False):
        if self.task_handler is not None:
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
    def __init__(self, process_id, task_handler: TaskHandler | None):
        super().__init__(task_handler)
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


from dataclasses import dataclass
from time import time


class ExampleEchoProcess(AbstractProcess):
    def __init__(self, process_id, task_handler: TaskHandler | None, is_init=False):
        super().__init__(task_handler)
        self.process_id = process_id
        self.is_init = is_init

    def get_id(self):
        return self.process_id

    def is_init_process(self):
        return self.is_init

    def is_in_terminal_state(self) -> bool:
        return False

    def _on_receive_message_(self, message):
        if message == AbstractProcess.kick_off_message:
            message = ExampleEchoProcess.MyMessage()
            message.counter = 0
            message.time_stamp = time()
        print(f"Process: {self.process_id}")
        print(message.get_string())
        new_message = ExampleEchoProcess.MyMessage()
        new_message.counter = message.counter + 1
        new_message.time_stamp = time()

        for receiver_id in self.channel_communication_provider.get_available_process_id():
            self.channel_communication_provider.send_message(receiver_id, new_message)

    @dataclass
    class MyMessage:
        counter = 0
        time_stamp = 0

        def get_string(self): return f"Hi for {self.counter} time after {time() - self.time_stamp}"
