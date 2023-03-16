from distributed_process import DistributedProcess
import random
import time
import threading

class Channel:
    def __init__(self, distributed_process : DistributedProcess):
        self.distributed_process_to_send = distributed_process

    def send(self, message):
        thread = threading.Thread(target=self.send_with_delay, args=(message,))
        thread.start()

    def send_with_delay(self, message):
        delay = random.randint(0, 9)
        time.sleep(delay)
        self.distributed_process_to_send.receive(message)

