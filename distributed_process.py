
class DistributedProcess:
    def __init__(self, unique_id: int, neighbors: list):
        self.unique_id = unique_id
        self.neighbors = neighbors

    def start(self):
        # running algo code
        pass

    def stop(self):
        pass

    def receive(self, message, sender):
        pass

    def send(self, message):
        pass



    # graph -> n x n

    # assign unique number to each process
    # list of channels -> process
