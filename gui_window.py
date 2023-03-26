from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QFileDialog, QAction, QWidget, QLabel, QComboBox, \
    QGridLayout, QLineEdit, QGroupBox, QVBoxLayout
from PyQt5.QtGui import QPainter, QPen, QBrush, QPolygon, QFont, QPainterPath, QColor
from PyQt5.QtCore import QPoint, QLine, QRect, QLineF, QTimer, QCoreApplication, QThread, pyqtSignal
from PyQt5.QtCore import Qt
import math
import copy
import time
import csv
import os
import sys

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

class MessageTraveller(QThread):
    message_changed = pyqtSignal()

    def __init__(self, message):
        super(MessageTraveller, self).__init__()
        self.message = message

    def run(self):
        while True:
            self.message_changed.emit()
            time.sleep(1)

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

        print(self.points)

    def paintEvent(self, event):
        if not self.stopped and self.point is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Set pen and brush for the envelope shape
            envelope_pen = QPen(QColor(255, 255, 255))
            envelope_brush = QBrush(QColor(225, 225, 225))
            painter.setPen(envelope_pen)
            painter.setBrush(envelope_brush)
            # Draw envelope shape
            print("drawing message")
            print(self.cur_point)
            self.point = self.points[self.cur_point]
            print(self.point)
            self.draw_message(painter)
            painter.end()
            self.update_position()

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

        if self.point is None:
            if self.parent() is not None and self.parent().layout() is not None:
                print("checks passed")

            if self.parent() is not None and self.parent().layout() is not None and self.parent().layout().indexOf(
                    self) != -1:
                print("second check passed")

            timer = QTimer(self)
            timer.setSingleShot(True)

            # Connect the timer's timeout signal to a function that will remove the widget
            timer.timeout.connect(self.deleteLater)

            # Start the timer with a 2 second delay
            timer.start(2000)

    def draw_message(self, painter):
        envelope_path = QPainterPath()
        envelope_path.moveTo(self.point.x(), self.point.y())
        envelope_path.lineTo(self.point.x() - 25, self.point.y())
        envelope_path.lineTo(self.point.x() - 25, self.point.y() - 50)
        envelope_path.lineTo(self.point.x() + 25, self.point.y() - 50)
        envelope_path.lineTo(self.point.x() + 25, self.point.y())

        envelope_path.lineTo(self.point.x(), self.point.y())

        painter.drawPath(envelope_path)

        # Set pen and brush for the arrow shape
        arrow_pen = QPen(QColor(0, 0, 0))
        arrow_brush = QBrush(QColor(0, 0, 0))
        painter.setPen(arrow_pen)
        painter.setBrush(arrow_brush)

        # Draw arrow shape
        arrow_path = QPainterPath()
        arrow_path.moveTo(self.point.x() - 20, self.point.y() - 40)
        arrow_path.lineTo(self.point.x(), self.point.y() - 20)
        arrow_path.lineTo(self.point.x() + 20, self.point.y() - 40)
        painter.drawPath(arrow_path)

    def stop(self):
        self.stopped = True

    def resume(self):
        self.stopped = False


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_variables()
        self.init_UI()
        self.is_graph_uploaded = False
        self.window.setAttribute(Qt.WA_TranslucentBackground)

        bar = self.window.menuBar()
        file = bar.addMenu("File")
        file.addAction("Upload graph from file")
        file.triggered[QAction].connect(self.file_menu_selected)

    def init_variables(self):
        self.point_to_draw = None
        desktop = QDesktopWidget().availableGeometry()
        self.all_width = desktop.width()
        self.all_height = desktop.height()

        self.menu_width = 450
        self.menu_height = 450

        self.window_width = self.all_width - self.menu_width

        self.ellipse_radius = 55
        self.first_process = [70, 70]
        self.center = QPoint(self.window_width / 2, self.all_height / 2)
        print(self.center)

        self.radius = min(self.window_width//2, self.all_height//2) - 2 * self.ellipse_radius

        self.stopped = False
        print(self.radius)

    def init_UI(self):
        self.window = QMainWindow()
        self.window.setCentralWidget(self)
        self.labels = []

        self.window.setFixedSize(self.all_width, self.all_height)
        self.window.setWindowTitle("Distributed computations modulation")
        self.window.show()

        self.central_widget = QWidget()

        """
        for i in range(5):
            self.label_1 = QLabel('round label', self)
            # moving position
            self.label_1.move(100 * i , 100 * i)
            self.label_1.resize(80, 80)
            self.labels
        self.window.show()
        """

    def file_menu_selected(self, q):
        print("triggered")

        filename, second = QFileDialog.getOpenFileName(self.window, "Open file", "")

        with open(filename, newline='') as csvfile:
            data_reader = csv.reader(csvfile, delimiter=' ', quotechar='"')
            data = []
            for row in data_reader:
                data.append([int(x) for x in row])

        self.graph = data
        self.processes_size = len(data)
        self.rotation_degree = 360 / len(data)
        self.is_graph_uploaded = True
        self.fill_labels()
        self.paint_menu_window()
        message = Message(self.vertexes[1], self.vertexes[2], [self.window.width(), self.window.height()], self)
        self.layout().addWidget(message)
        self.thread = MessageTraveller(message)
        self.thread.message_changed.connect(self.update)
        self.thread.start()
        #timer = QTimer(self)
        #timer.setSingleShot(True)
        #self.layout().removeWidget(message)
        # Connect the timer's timeout signal to a function that will remove the widget
        #timer.timeout.connect(lambda : self.layout().removeWidget(message))

        # Start the timer with a 2 second delay
        #timer.start(4000)

        #self.paint_message_traversal(message_delay, 1, 2)


    def show(self):
        super().show()
        self.window.show()

    def paintEvent(self, event):
       if self.is_graph_uploaded:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.black, 5, Qt.SolidLine))
            painter.setBrush(QBrush(Qt.darkGreen, Qt.SolidPattern))
            self.paint_graph(painter)

            painter.setBrush(QBrush())
            painter.drawRect(self.all_width - self.menu_width - 1, 0, self.menu_width + 1, self.menu_height + 1)

    def paint_process(self, painter, x, y):
        painter.drawEllipse(x, y, self.ellipse_radius, self.ellipse_radius)

    def on_stop_click(self):
        if not self.stopped:
            self.stopped = True
            self.stop_algo.setText("Resume")
        else:
            self.stopped = False
            self.stop_algo.setText("Stop")


    def paint_menu_window(self):
        painter = QPainter(self)
        self.menu_label = QLabel('Menu', self)
        self.menu_label.setFont(QFont("Arial", 22, QFont.Bold))
        self.menu_label.setStyleSheet("color: Blue;")
       # menu_label.move(self.all_width - self.menu_width/2, 20)

        self.select_algorithm = QLabel('Select algorithm')
        self.select_algorithm.setFont(QFont("Arial", 16))
        self.select_algorithm.adjustSize()
        self.select_algorithm.setStyleSheet("color: Blue;")


        self.algo_selected = QComboBox()
        self.algo_selected.addItem('Snapshot collection')
        self.algo_selected.addItem('Garbage collection')
        self.algo_selected.addItem('Echo')
        self.algo_selected.addItem('Wave')
        self.algo_selected.setFont(QFont("Arial", 16))


        self.select_delivery_chance = QLabel('Input message delivery chance')
        self.select_delivery_chance.setFont(QFont("Arial", 16))
        self.select_delivery_chance.setStyleSheet("color: Blue;")
        self.select_delivery_chance.adjustSize()

        self.delivery_chance= QLineEdit(self)
        self.delivery_chance.move(20, 20)
        self.delivery_chance.resize(280, 40)
        self.delivery_chance.setFont(QFont("Arial", 16))
        self.delivery_chance.setText("1")

        self.select_channel_type = QLabel('Select communication channel type')
        self.select_channel_type.setFont(QFont("Arial", 16))
        self.select_channel_type.setStyleSheet("color: Blue;")
        self.select_channel_type.adjustSize()

        self.fifo_channel_type = QtWidgets.QRadioButton()
        self.fifo_channel_type.setText("FIFO")
        self.fifo_channel_type.setFont(QFont("Arial", 16))
        self.regular_channel_type = QtWidgets.QRadioButton()
        self.regular_channel_type.setText("Regular")
        self.regular_channel_type.setFont(QFont("Arial", 16))

        self.select_initiator = QLabel('Select algorithm initiator')
        self.select_initiator.setFont(QFont("Arial", 16))
        self.select_initiator.adjustSize()
        self.select_initiator.setStyleSheet("color: Blue;")

        self.initiator_selected = QComboBox()
        for i in range(len(self.graph)):
            self.initiator_selected.addItem('Node ' + str(i))
        self.initiator_selected.setFont(QFont("Arial", 16))

        self.start_algo = QtWidgets.QPushButton("Start")
        self.start_algo.setFont(QFont("Arial", 18))
        self.start_algo.setFixedSize(200, 50)

        self.stop_algo = QtWidgets.QPushButton("Stop")
        self.stop_algo.setFont(QFont("Arial", 18))
        self.stop_algo.setFixedSize(200, 50)
        self.stop_algo.clicked.connect(self.on_stop_click)


        layout = QGridLayout()

        layout.addWidget(self.menu_label, 0, 0, 2, 2, Qt.AlignCenter)
        layout.addWidget(self.select_algorithm, 2, 0)
        layout.addWidget(self.algo_selected, 2, 1)
        layout.addWidget(self.select_delivery_chance, 3, 0)
        layout.addWidget(self.delivery_chance, 3, 1, Qt.AlignCenter)
        layout.addWidget(self.select_channel_type, 4, 0, 2, 0, Qt.AlignLeft)
        layout.addWidget(self.fifo_channel_type, 4, 1, Qt.AlignRight)
        layout.addWidget(self.regular_channel_type, 5, 1, Qt.AlignRight)
        layout.addWidget(self.select_initiator, 6, 0)
        layout.addWidget(self.initiator_selected, 6, 1)
        layout.addWidget(self.start_algo, 7, 0, 2, 0, Qt.AlignCenter)
        layout.addWidget(self.stop_algo, 8, 0, 2, 0, Qt.AlignCenter)

        rect = QRect(self.all_width - self.menu_width, 0, self.menu_width, self.menu_height)

        widget = QWidget()
        widget.setLayout(layout)
        widget.setGeometry(rect)

        self.layout().addWidget(widget)

    def fill_labels(self):
        self.vertexes = []
        self.labels = []
        for i in range(len(self.graph)):
            angle = i * 2 * math.pi / len(self.graph)
            x = self.center.x() + int(self.radius * math.cos(angle))
            y = self.center.y() + int(self.radius * math.sin(angle))
            vertex = QPoint(x, y)
            self.vertexes.append(vertex)
            label = QLabel('Node ' + str(i), self)
            label.setFont(QFont("Arial", 16))
            label.setStyleSheet("color: white;")
            label.move(vertex)
            self.layout().addWidget(label)
            self.labels.append(label)

    def paint_graph(self, painter):
        for vertex in self.vertexes:
            painter.drawEllipse(vertex, self.ellipse_radius, self.ellipse_radius)

        self.lines = []

        for i in range(len(self.graph)):
            for j in range(len(self.graph[i])):
                if self.graph[i][j] == 1 and i != j:
                    l = QLine(self.vertexes[i], self.vertexes[j])
                    self.lines.append(l)
                    painter.drawLine(l)

def application_start():
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())

