import time

from PyQt5.QtCore import QLineF, QTimer
from PyQt5.QtGui import QPainterPath, QPainter, QPen, QBrush, QColor
from PyQt5.QtWidgets import QWidget

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

class Message(QWidget):
    def __init__(self, sender, recipient, size, parent = None):
        super(Message, self).__init__(parent)
        self.setParent(parent)
        #self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setFixedSize(size[0], size[1])

        self.point = sender
        self.stopped = False

        line = QLineF(sender.x(), sender.y(), recipient.x(), recipient.y())
        print("line ")
        print(line.length())
        print(line.center())
        self.points = divide_line(line, message_delay)
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
            self.timer = QTimer(self)


    def update_position(self):
        if self.cur_point == message_delay - 1:
            self.cur_point = message_delay - 1
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
