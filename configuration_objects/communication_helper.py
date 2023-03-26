from distributed_objects.channel import AbstractChannel, ChannelWrapper
from distributed_objects.process import AbstractProcess
from typing import Dict, Any, List


class ChannelInfoHolder:
    channel_placeholder = "No channel"

    def __init__(self):
        self.communication_dict: Dict[Any, Dict[Any, ChannelWrapper]] = {}

    def set_channel_for(self, sender_id, receiver_id, channel: AbstractChannel | None):
        if self.communication_dict.get(sender_id) is not None:
            self.communication_dict.get(sender_id)[receiver_id] = ChannelWrapper(channel, sender_id, receiver_id)
        else:
            self.communication_dict[sender_id] = {receiver_id: ChannelWrapper(channel, sender_id, receiver_id)}

    def clear_channels(self):
        self.communication_dict = {}

    def get_channel_for(self, sender_id, receiver_id) -> ChannelWrapper | None:
        channel = self.communication_dict[sender_id][receiver_id]
        return channel if channel is ChannelWrapper else None

    def get_available_channels_for(self, sender_id) -> List[ChannelWrapper]:
        channels = self.communication_dict[sender_id]
        return [] if channels is None else [chan for chan in channels.values() if chan.inner_channel]

    def get_available_receiver_id_for(self, sender_id) -> List:
        return [ch.receiver_id for ch in self.get_available_channels_for(sender_id)]

    def get_all_channels(self) -> List[ChannelWrapper]:
        result = []
        for channels in self.communication_dict.values():
            for ch in channels.values():
                if ch.inner_channel:
                    result.append(ch)
        return result


class ProcessInfoHolder:
    process_placeholder = "No process set"

    def __init__(self):
        self.processes_dictionary: Dict[Any, AbstractProcess] = {}

    def set_process(self, process: AbstractProcess):
        self.processes_dictionary[process.get_id()] = process

    def set_placeholder(self, process_id):
        self.processes_dictionary[process_id] = ProcessInfoHolder.process_placeholder

    def clear_processes(self):
        self.processes_dictionary = {}

    def update_processes(self, processes: List[AbstractProcess]):
        self.processes_dictionary.update([(p.get_id(), p) for p in processes])

    def get_process(self, process_id) -> AbstractProcess | None:
        return self.processes_dictionary.get(process_id)

    def get_all_processes(self) -> List[AbstractProcess]:
        return list(self.processes_dictionary.values())


class CommunicationHelper:
    def __init__(self):
        self.channel_info_holder = ChannelInfoHolder()
        self.process_info_holder = ProcessInfoHolder()
        self.init_processes: Dict[Any, AbstractProcess] = {}

    def check_is_everything_ok(self, should_print: bool) -> bool:
        not_set_processes_with_id = []

        for process_id, process in self.process_info_holder.processes_dictionary.items():
            if process == ProcessInfoHolder.process_placeholder:
                not_set_processes_with_id.append(process_id)

        not_set_channels: List[ChannelWrapper] = []
        not_found_process_id = set()
        for (sender_id, receiver_dict) in self.channel_info_holder.communication_dict.items():
            if self.process_info_holder.get_process(sender_id) is None:
                not_found_process_id.add(sender_id)
            for (receiver_id, channel) in receiver_dict.items():
                if self.process_info_holder.get_process(receiver_id) is None:
                    not_found_process_id.add(receiver_id)
                if not channel.inner_channel:
                    not_set_channels.append(channel)

        if should_print:
            if not_set_processes_with_id:
                print(f"Not set process with ids {not_set_processes_with_id}")
            for channel in not_set_channels:
                print(f"Not set channel from {channel.sender_id} to {channel.receiver_id}")
            if not_found_process_id:
                print(f"Not found process with ids {not_found_process_id} from communication graph")

        return not not_set_processes_with_id and not not_set_channels and not not_found_process_id

    def get_channel_for(self, sender_id, receiver_id) -> AbstractChannel | None:
        return self.channel_info_holder.get_channel_for(sender_id, receiver_id)

    def set_channel_for(self, channel: AbstractChannel, sender_id, receiver_id):
        self.channel_info_holder.set_channel_for(sender_id, receiver_id, channel)

    def get_process_with_id(self, process_id) -> AbstractProcess | None:
        return self.process_info_holder.get_process(process_id)

    def set_process(self, process: AbstractProcess):
        self.process_info_holder.set_process(process)

    def create_graph_file(self, path):
        """
        TODO: store here parameters and classes of process and channels
        TODO: so you don't have to each time setup distributed system
        """

        pass

    def parse_simple_graph(self, path):
        """
        the file contains only matrix and process id's are [0,1,2...]
        """

        pass

    def parse_graph(self, path):
        self.process_info_holder.clear_processes()
        self.channel_info_holder.clear_channels()
        with open(path) as file:
            lines = file.readlines()

        for line in lines:
            data = [s.strip() for s in line.split(":", 1)]
            sender_id = data[0]
            self.process_info_holder.set_placeholder(sender_id)
            receivers_ids = [s.strip() for s in data[1].split(",")]
            for receiver_id in receivers_ids:
                self.process_info_holder.set_placeholder(receiver_id)
                self.channel_info_holder.set_channel_for(sender_id, receiver_id, None)
