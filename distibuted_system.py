from taskhandler import TaskHandler, Task
from distributed_objects.channel import AbstractChannel
from typing import List
from distributed_objects.process import ChannelCommunicationProvider, AbstractProcess
from configuration_objects.communication_helper import CommunicationHelper
from looper import ProcessLooper, QThreadLooper, ThreadLooper
from enum import Enum


class DistributedSystem:
    """
    ALL THE USER FUNCTIONS ARE MAIN THREAD ONLY
    """

    def __init__(self, communication_helper=None):
        self.main_task_handler: TaskHandler | None = None  # DistributedSystem's handler to avoid main thread blocking
        self.channels_task_handler: TaskHandler | None = None
        self.processors: TaskHandler | None = None
        self.has_started = False
        if communication_helper:
            self.communication_helper = communication_helper
        else:
            self.communication_helper = CommunicationHelper()

    def pause(self):
        self.main_task_handler.pause()
        for process in self.communication_helper.get_all_processes():
            process.pause()

        for channel in self.communication_helper.get_all_channels():
            channel.pause()

    def unpause(self):
        self.main_task_handler.unpause()
        for process in self.communication_helper.get_all_processes():
            process.unpause()

        for channel in self.communication_helper.get_all_channels():
            channel.unpause()

    def stop(self, is_instant=False):
        for process in self.communication_helper.get_all_processes():
            process.stop(is_instant)

        for channel in self.communication_helper.get_all_channels():
            channel.stop(is_instant)

        if is_instant:
            self.main_task_handler.instant_stop()
        else:
            self.main_task_handler.stop()

    def start(self):
        self.main_task_handler.start()
        init_processes = [proc for proc in self.communication_helper.get_all_processes() if proc.is_init_process()]

        def component_start():
            for proc in init_processes:
                proc.receive_message(AbstractProcess.kick_off_message)

            for process in self.communication_helper.get_all_processes():
                process.start()

            for channel in self.communication_helper.get_all_channels():
                channel.start()

        if not self.has_started:
            self.has_started = True
            self.main_task_handler.schedule_action(component_start)

    def get_snapshot(self):
        self.pause()
        channels_information = [channel.get_current_state_information() for channel in
                                self.communication_helper.get_all_channels()]
        process_information = [proc.get_current_state_information() for proc in
                               self.communication_helper.get_all_processes()]
        self.unpause()

        return process_information, channels_information

    def disable_process(self, process_id):
        process = self.communication_helper.get_process_with_id(process_id)
        if process:
            process.disable()

    def enable_process(self, process_id):
        process = self.communication_helper.get_process_with_id(process_id)
        if process:
            process.enable()

    def disable_channel(self, sender_id, receiver_id):
        channel = self.communication_helper.get_channel_for(sender_id, receiver_id)
        if channel:
            channel.disable()

    def enable_channel(self, sender_id, receiver_id):
        channel = self.communication_helper.get_channel_for(sender_id, receiver_id)
        if channel:
            channel.enable()

    def __set_channel__(self, channel: AbstractChannel, sender_id, receiver_id):
        self.communication_helper.set_channel_for(channel, sender_id, receiver_id)

    def __set_process__(self, process: AbstractProcess):
        process.set_channel_communication_provider(
            DistributedSystem.ChannelCommunicationProviderImpl(
                self,
                process.get_id()
            )
        )
        self.communication_helper.set_process(process)

    def __set_communication_graph__(self, path):
        self.communication_helper.parse_graph(path)

    def __schedule_instant_task__(self, action):
        task = Task(
            action,
            None
        )
        self.main_task_handler.schedule_task(task)

    def __create_channel_message_callback__(self, receiver_id):
        """
        callback to send message to process
        :param receiver_id: id of a process which should receive the message
        :return: callback to communicate with distributed system in proper way
        """

        def send_to_process(message):
            process = self.communication_helper.get_process_with_id(receiver_id)
            if process is None:
                return
            process.receive_message(message)

        def callback(message):
            self.__schedule_instant_task__(
                lambda: send_to_process(message)
            )

        return callback

    def __schedule_send_message_channel__(self, sender_id, receiver_id, message):
        """
        simulation of message delivery inside channel
        tries to find proper communication channel and simulate delivery
        :param sender_id: id of sender process
        :param receiver_id: id of receiver process
        :param message: message to deliver
        """

        def try_send_message() -> bool:
            communication_channel = self.communication_helper.get_channel_for(sender_id, receiver_id)
            if not isinstance(communication_channel, AbstractChannel):
                return False

            communication_channel.deliver_message(
                self.__create_channel_message_callback__(receiver_id),
                message
            )
            return True

        self.__schedule_instant_task__(try_send_message)

    class ChannelCommunicationProviderImpl(ChannelCommunicationProvider):
        def __init__(self, distributed_system, sender_id):
            self.distributed_system: DistributedSystem = distributed_system
            self.sender_id = sender_id

        def get_available_process_id(self) -> List:
            return list(
                self.distributed_system.communication_helper.get_available_receivers_id_for(self.sender_id)
            )

        def send_message(self, receiver_id, message) -> None:
            self.distributed_system.main_task_handler.schedule_action(
                lambda: self.distributed_system.__schedule_send_message_channel__(
                    self.sender_id,
                    receiver_id,
                    message
                )
            )


class DistributedSystemBuilder:
    class LooperType(Enum):
        Thread = 1
        QThread = 2
        Process = 3

    def __init__(self):
        self.communication_helper = CommunicationHelper()
        self.distributed_system = DistributedSystem(self.communication_helper)
        self.one_thread_model = False
        self.thread_per_channel_model = True
        self.thread_per_process = True
        self.looper_type = DistributedSystemBuilder.LooperType.QThread
        self.loop_delay_ms = 10

    def check(self):
        self.communication_helper.check_is_everything_ok(True)
        return self

    def enable_one_thread_model(self, is_enabled):
        self.one_thread_model = is_enabled
        return self

    def enable_thread_per_channel_model(self, is_enabled):
        self.thread_per_channel_model = is_enabled
        return self

    def enable_thread_per_process(self, is_enabled):
        self.thread_per_process = is_enabled
        return self

    def set_async_model(self, loop_type, loop_delay_ms: int | None):
        self.loop_delay_ms = loop_delay_ms
        self.looper_type = loop_type
        return self

    def add_channel(self, channel: AbstractChannel, sender_id, receiver_id):
        self.distributed_system.__set_channel__(channel, sender_id, receiver_id)
        return self

    def remove_channel(self, sender_id, receiver_id):
        self.communication_helper.remove_channel_for(sender_id, receiver_id)

    def add_process(self, proc: AbstractProcess):
        self.distributed_system.__set_process__(proc)
        return self

    def remove_process(self, process_id):
        self.communication_helper.remove_process(process_id)

    def load_from_file(self, path):
        self.communication_helper.parse_graph(path)
        return self

    def __get_new_looper__(self):
        if self.looper_type == DistributedSystemBuilder.LooperType.QThread:
            return QThreadLooper(self.loop_delay_ms)
        elif self.looper_type == DistributedSystemBuilder.LooperType.Thread:
            return ThreadLooper(self.loop_delay_ms)
        else:
            return ProcessLooper(self.loop_delay_ms)

    def __get_new_task_handler__(self) -> TaskHandler:
        looper = self.__get_new_looper__()
        return TaskHandler(looper)

    def build(self) -> DistributedSystem:
        main_task_handler = self.__get_new_task_handler__()
        self.distributed_system.main_task_handler = main_task_handler
        if self.one_thread_model:
            for proc in self.communication_helper.get_all_processes():
                proc.set_task_handler(None)
            for channel in self.communication_helper.get_all_channels():
                channel.set_task_handler(main_task_handler)
        else:
            if self.thread_per_process:
                for proc in self.communication_helper.get_all_processes():
                    proc_task_handler = self.__get_new_task_handler__()
                    proc.set_task_handler(proc_task_handler)
            else:
                for proc in self.communication_helper.get_all_processes():
                    proc.set_task_handler(None)

            if self.thread_per_channel_model:
                for channel in self.communication_helper.get_all_channels():
                    channel_task_handler = self.__get_new_task_handler__()
                    channel.set_task_handler(channel_task_handler)
            else:
                for channel in self.communication_helper.get_all_channels():
                    channel.set_task_handler(main_task_handler)

        return self.distributed_system
