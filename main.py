# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


# Plan:
# 1. Create instances distributed-initializer, distributed-process
# 2.

from distributed_process import DistributedProcess
from distributed_initializer import DistributedInitializer
from messaging_system import MessagingSystem


def get_neighbors_of_process(process_id, graph):
    neighbors = []
    for i in range(len(graph[process_id])):
        if process_id != i:
            if graph[process_id][i] == 1:
                neighbors.append(i)

    return neighbors


if __name__ == '__main__':
    # fully-connected square
    test_graph = [[1, 1, 1, 1],
                  [1, 1, 1, 1],
                  [1, 1, 1, 1],
                  [1, 1, 1, 1]]
    processes = []
    for i in range(len(test_graph)):
        processes.append(DistributedProcess(i, get_neighbors_of_process(i, test_graph)))

    messaging_system = MessagingSystem(test_graph, processes)
    

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
