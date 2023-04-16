import time

from PyQt5.QtCore import QLineF, QTimer, pyqtSignal, QPropertyAnimation, QPoint, pyqtProperty
from PyQt5.QtGui import QPainterPath, QPainter, QPen, QBrush, QColor
from PyQt5.QtWidgets import QWidget
from distributed_objects.channel import AbstractChannel
from task_handler.taskhandler import TaskInfo
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


from task_handler.taskhandler import TaskHandler


class MessageInfoDelayChannel(AbstractChannel):
    def __init__(self, sender_id,
                 receiver_id,
                 delay_range,
                 message_info_callback,
                 task_handler: TaskHandler | None
                 ):
        super().__init__(task_handler)
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


def divide_line(line, n):
    # Calculate the length of the line
    line_length = line.length()

    # Determine the distance between each point
    distance_between_points = line_length / (n - 1)

    # Create a list to hold the points
    points = []

    if line_length != 0:
        # Determine the points along the line
        for i in range(int(n)):
            # Calculate the position of the current point
            position = line.pointAt(i * distance_between_points / line.length())
            # Add the point to the list
            points.append(position)

    print(points)
    return points


class QMessage(QWidget):
    is_deleted = pyqtSignal()

    def __init__(self, sender, recipient, delay, parent=None):
        super(QMessage, self).__init__(parent)
        self.delay = delay
        self.setParent(parent)
        self.sender = sender
        self.recipient = recipient
        self.id = str(sender) + str(recipient)
        self.first_point_paint = False

    def set_size(self, size):
        self.setFixedSize(size[0], size[1])

    def set_graph(self, graph):
        self.graph = graph
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self._position = graph[self.sender]
        self.stopped = False

        line = QLineF(graph[self.sender].x(), graph[self.sender].y(), graph[self.recipient].x(),
                      graph[self.recipient].y())
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

    def paintEvent(self, event):
        # print("Paint called")
        if self._position is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Set pen and brush for the envelope shape
            envelope_pen = QPen(QColor(255, 255, 255))
            envelope_brush = QBrush(QColor(225, 225, 225))
            painter.setPen(envelope_pen)
            painter.setBrush(envelope_brush)
            # Draw envelope shape
            # self.point = self.points[self.cur_point]
            self.draw_message(painter)
            # self.update_position()
            # self.timer = QTimer(self)

    def update_position(self):
        if self.cur_point == int(self.delay) - 2:
            self.cur_point = int(self.delay) - 2
            self._position = None

        if not self.stopped:
            print(time.time())
            print("repainted")
        else:
            self.cur_point = self.cur_point - 1

        self.cur_point = self.cur_point + 1
        self.delete_if_needed()

    def delete_if_needed(self):
        if self._position is None:
            self.delete_and_notify()
            # self.timer.setSingleShot(True)

            # Connect the timer's timeout signal to a function that will remove the widget
            # self.timer.timeout.connect(self.delete_and_notify)

            # Start the timer with a 2 second delay
            # self.timer.start(1000)

    def delete_and_notify(self):
        self.anim.stop()
        self.is_deleted.emit()
        self.deleteLater()

    def draw_message(self, painter):
        envelope_path = QPainterPath()
        # print("Position! ")
        # print(self._position)
        # painter.drawRect(self._position.x(), self._position.y(), self._position.x() - 20, self._position.y() - 20)

        envelope_path.moveTo(self._position.x(), self._position.y())
        envelope_path.lineTo(self._position.x() - 25, self._position.y())
        envelope_path.lineTo(self._position.x() - 25, self._position.y() - 50)
        envelope_path.lineTo(self._position.x() + 25, self._position.y() - 50)
        envelope_path.lineTo(self._position.x() + 25, self._position.y())

        envelope_path.lineTo(self._position.x(), self._position.y())
        painter.drawPath(envelope_path)

        # Set pen and brush for the arrow shape
        arrow_pen = QPen(QColor(0, 0, 0))
        arrow_brush = QBrush(QColor(0, 0, 0))
        painter.setPen(arrow_pen)
        painter.setBrush(arrow_brush)

        # Draw arrow shape
        arrow_path = QPainterPath()
        arrow_path.moveTo(self._position.x() - 20, self._position.y() - 40)
        arrow_path.lineTo(self._position.x(), self._position.y() - 20)
        arrow_path.lineTo(self._position.x() + 20, self._position.y() - 40)
        painter.drawPath(arrow_path)

    def stop(self):
        self.stopped = True

    def resume(self):
        self.stopped = False

    def get_position(self):
        return self._position

    def set_position(self, position):
        # print("Position ")
        # print(position)
        self._position = position
        self.update()

    position = pyqtProperty(QPoint, fset=set_position, fget=get_position)

    def animate(self):
        self.anim.start(self.anim.DeleteWhenStopped)

    def build_animation(self):
        self.anim = QPropertyAnimation(self, b'position')
        self.anim.setStartValue(self.graph[self.sender])
        self.anim.setEndValue(self.graph[self.recipient])
        self.anim.setDuration(int(1000 * self.delay))
        return self.anim

    def get_animation(self):
        return self.anim
