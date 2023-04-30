from dataclasses import dataclass

from task_handler.taskhandler import TaskHandler, Task
from task_handler.task_scheduler import TaskWrapper
from distributed_objects.channel import AbstractChannel
from typing import List
from distributed_objects.process import ChannelCommunicationProvider, AbstractProcess
from configuration_objects.communication_helper import CommunicationHelper
from task_handler.looper import ProcessLooper, QThreadLooper, ThreadLooper
from threading import Lock
from enum import Enum

@dataclass
class InternalAction:
    action = ""

    def __str__(self) -> str:
        return self.action

class DistributedSystem:
    """
    ALL THE USER FUNCTIONS ARE MAIN THREAD ONLY
    """

    def __init__(self, communication_helper=None):
        self.main_task_handler: TaskHandler | None = None  # DistributedSystem's handler to avoid main thread blocking
        self.has_started = False
        self.is_paused = False
        self.execution_log_lock = Lock()
        self.execution_log = ()
        if communication_helper:
            self.communication_helper = communication_helper
        else:
            self.communication_helper = CommunicationHelper()

    def pause(self):
        self.is_paused = True
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

        self.is_paused = False

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
            self.__clear_execution_log__()
            self.has_started = True
            self.main_task_handler.schedule_action(component_start)

    def get_snapshot(self):
        was_paused = self.is_paused
        self.pause()
        channels_information = [channel.get_current_state_information() for channel in
                                self.communication_helper.get_all_channels()]
        process_information = [proc.get_current_state_information() for proc in
                               self.communication_helper.get_all_processes()]
        if not was_paused:
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

    def __clear_execution_log__(self):
        with self.execution_log_lock:
            self.execution_log = ()

    def __add_execution_log__(self, value):
        with self.execution_log_lock:
            self.execution_log = self.execution_log + (value,)

    def get_execution_log(self):
        process_states, _ = self.get_snapshot()
        log = self.execution_log
        if process_states:
            log += ("*************PROCESS STATES************",)
        for proc_state in process_states:
            log += (proc_state,)
        if process_states:
            log += ("***************************************",)
        return log

    def __schedule_instant_task__(self, task: Task):
        if isinstance(task, DistributedSystem.MessageSendTask):
            task_to_schedule = TaskWrapper(
                task,
                lambda: self.print_task_log(task)
            )
        elif isinstance(task, DistributedSystem.MessageReceiveTask):
            task_to_schedule = TaskWrapper(
                task,
                lambda: self.print_second_task_log(task)
            )
        else:
            task_to_schedule = task

        self.main_task_handler.schedule_task(task_to_schedule)

    def print_task_log(self, task : Task):
        if isinstance(task.message, InternalAction):
            self.__add_execution_log__(
                f"{task.message}"
            )
        else:
            self.__add_execution_log__(
                f"Process {task.sender_id} send to {task.receiver_id} message: {task.message}"
            )

    def print_second_task_log(self, task : Task):
        if isinstance(task.message, InternalAction):
            self.__add_execution_log__(
                f"{task.message}"
            )
        else:
            self.__add_execution_log__(
                f"Process {task.receiver_id} received from {task.sender_id} message: {task.message}"
            )

    class MessageReceiveTask(Task):
        def __init__(self,
                     distributed_system,
                     sender_id,
                     receiver_id,
                     message,
                     ):
            self.distributed_system = distributed_system
            self.sender_id = sender_id
            self.receiver_id = receiver_id
            self.message = message
            self.action = self.__receive_message__

        def __receive_message__(self):
            process = self \
                .distributed_system \
                .communication_helper \
                .get_process_with_id(self.receiver_id)
            if process is None:
                return
            process.receive_message(self.message)

    class MessageSendTask(Task):
        def __init__(self,
                     distributed_system,
                     sender_id,
                     receiver_id,
                     message,
                     ):
            self.distributed_system = distributed_system
            self.sender_id = sender_id
            self.receiver_id = receiver_id
            self.message = message
            self.action = self.try_send_message

        def try_send_message(self) -> bool:
            communication_channel = self \
                .distributed_system \
                .communication_helper \
                .get_channel_for(self.sender_id, self.receiver_id)

            if not isinstance(communication_channel, AbstractChannel):
                return False

            communication_channel.deliver_message(
                lambda message: self.distributed_system.__schedule_instant_task__(
                    DistributedSystem.MessageReceiveTask(
                        self.distributed_system,
                        self.sender_id,
                        self.receiver_id,
                        message
                    )
                ),
                self.message
            )
            return True

    class ChannelCommunicationProviderImpl(ChannelCommunicationProvider):
        def __init__(self, distributed_system, sender_id):
            self.distributed_system: DistributedSystem = distributed_system
            self.sender_id = sender_id

        def get_available_process_id(self) -> List:
            return list(
                self.distributed_system.communication_helper.get_available_receivers_id_for(self.sender_id)
            )

        def send_message(self, receiver_id, message) -> None:
            self.distributed_system.__schedule_instant_task__(
                DistributedSystem.MessageSendTask(
                    self.distributed_system,
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
