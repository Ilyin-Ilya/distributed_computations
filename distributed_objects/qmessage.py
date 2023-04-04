import time

from PyQt5.QtCore import QLineF, QTimer
from PyQt5.QtGui import QPainterPath, QPainter, QPen, QBrush, QColor
from PyQt5.QtWidgets import QWidget
from distributed_objects.channel import AbstractChannel
from taskhandler import TaskInfo
from random import random
from threading import Lock


class MessageInfo:
    def __init__(self, sender_id, receiver_id, task_info: TaskInfo):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.task_info = task_info

    def get_sender_id(self):
        return self.sender_id

    def get_receiver_id(self):
        return self.receiver_id

    def get_total_delay(self):
        return self.task_info.get_delay()

    def get_time_spent(self):
        time_left = self.task_info.time_left()
        if time_left < 0:
            return 0
        return self.task_info.get_delay() - self.task_info.time_left()


class MessageInfoDelayChannel(AbstractChannel):
    def __init__(self, sender_id, receiver_id, delay_range, message_info_callback):
        super().__init__()
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message_info_callback = message_info_callback
        self.delay_range = delay_range
        self.is_enabled = True
        self.is_enabled_lock = Lock()

    def disable(self):
        with self.is_enabled_lock:
            self.is_enabled = False

    def enable(self):
        with self.is_enabled_lock:
            self.is_enabled = True

    def deliver_message(self, send_message_callback, message):
        if not self.is_enabled:
            return

        self.start()
        random_value = random()
        random_delay = self.delay_range[0] + (self.delay_range[1] - self.delay_range[0]) * random_value
        task_info = self.task_handler.schedule_action(
            lambda: send_message_callback(message),
            random_delay
        )

        message_info = MessageInfo(
            self.sender_id,
            self.receiver_id,
            task_info
        )

        self.message_info_callback(message_info)


message_delay = 10


def divide_line(line, n):
    # Calculate the length of the line
    line_length = line.length()

    # Determine the distance between each point
    distance_between_points = line_length / (n - 1)

    # Create a list to hold the points
    points = []

    # Determine the points along the line
    for i in range(n):
        # Calculate the position of the current point
        position = line.pointAt(i * distance_between_points / line.length())
        print("point")
        print(position)
        # Add the point to the list
        points.append(position)

    return points


class QMessage(QWidget):
    def __init__(self, sender, recipient, delay, parent=None):
        super(QMessage, self).__init__(parent)
        self.delay = delay
        self.setParent(parent)
        self.sender = sender
        self.recipient = recipient
        self.id = str(sender) + str(recipient)

    def set_size(self, size):
        self.setFixedSize(size[0], size[1])

    def set_graph(self, graph):
        self.graph = graph
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.point = graph[self.sender]
        self.stopped = False

        line = QLineF(graph[self.sender].x(), graph[self.sender].y(), graph[self.recipient].x(),
                      graph[self.recipient].y())
        print("line ")
        print(line.length())
        print(line.center())
        self.points = divide_line(line, self.delay)
        self.cur_point = 0
        self.envelopes = []
        self.arrows = []
        for i in range(len(self.points)):
            envelope_path = QPainterPath()
            envelope_path.moveTo(self.points[i].x(), self.points[i].y())
            envelope_path.lineTo(self.points[i].x() - 25, self.points[i].y())
            envelope_path.lineTo(self.points[i].x() - 25, self.points[i].y() - 50)
            envelope_path.lineTo(self.points[i].x() + 25, self.points[i].y() - 50)
            envelope_path.lineTo(self.points[i].x() + 25, self.points[i].y())

            envelope_path.lineTo(self.points[i].x(), self.points[i].y())
            self.envelopes.append(envelope_path)

            # Draw arrow shape
            arrow_path = QPainterPath()
            arrow_path.moveTo(self.points[i].x() - 20, self.points[i].y() - 40)
            arrow_path.lineTo(self.points[i].x(), self.points[i].y() - 20)
            arrow_path.lineTo(self.points[i].x() + 20, self.points[i].y() - 40)
            self.arrows.append(arrow_path)

        print(self.points)

    def paintEvent(self, event):
        if self.point is not None:
            print("message repainted " + str(self.delay))
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Set pen and brush for the envelope shape
            envelope_pen = QPen(QColor(255, 255, 255))
            envelope_brush = QBrush(QColor(225, 225, 225))
            painter.setPen(envelope_pen)
            painter.setBrush(envelope_brush)
            # Draw envelope shape
            self.point = self.points[self.cur_point]
            self.draw_message(painter)
            self.update_position()
            self.timer = QTimer(self)

    def update_position(self):
        if self.cur_point == self.delay - 1:
            self.cur_point = self.delay - 1
            self.point = None

        if not self.stopped:
            print(time.time())
            print("repainted")
        else:
            self.cur_point = self.cur_point - 1

        self.cur_point = self.cur_point + 1
        self.delete_if_needed()

    def delete_if_needed(self):
        if self.point is None:
            self.timer.setSingleShot(True)

            # Connect the timer's timeout signal to a function that will remove the widget
            self.timer.timeout.connect(self.deleteLater)

            # Start the timer with a 2 second delay
            self.timer.start(2000)

    def draw_message(self, painter):
        painter.drawPath(self.envelopes[self.cur_point])
        # Set pen and brush for the arrow shape
        arrow_pen = QPen(QColor(0, 0, 0))
        arrow_brush = QBrush(QColor(0, 0, 0))
        painter.setPen(arrow_pen)
        painter.setBrush(arrow_brush)
        painter.drawPath(self.arrows[self.cur_point])

    def stop(self):
        self.stopped = True

    def resume(self):
        self.stopped = False
