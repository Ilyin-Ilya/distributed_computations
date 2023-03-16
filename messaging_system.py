import random
import time
import threading

class MessagingSystem :
    def __init__(self, graph : list, processes : list):
        self.graph = graph
        self.processes = list

    def start(self):
        # running algo code
        pass

    def stop(self):
        pass

    def receive(self, message):
        pass

    def send(self, message, sender, recipient):
        thread = threading.Thread(target=self.send_with_delay, args=(message, sender, recipient))
        thread.start()

    def send_with_delay(self, message, sender, recipient):
        delay = random.randint(0, 9)
        time.sleep(delay)
        self.processes[recipient].receive(message, sender)
