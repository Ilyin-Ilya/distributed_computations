from random import random, randrange, randint

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QFileDialog, QAction, QWidget, QLabel, QComboBox, \
    QGridLayout, QLineEdit, QGroupBox, QVBoxLayout, QTextEdit
from PyQt5.QtGui import QPainter, QPen, QBrush, QPolygon, QFont, QPainterPath, QColor
from PyQt5.QtCore import QPoint, QLine, QRect, QLineF, QTimer, QCoreApplication, QThread, pyqtSignal, QMetaObject, \
    QPropertyAnimation, QParallelAnimationGroup
from PyQt5.QtCore import Qt, QObject
import math
import copy
import time
import csv
import os
import sys
from distibuted_system import DistributedSystem, DistributedSystemBuilder
from distributed_objects.qmessage import MessageInfoDelayChannel, MessageInfo, QMessage
from distributed_objects.process import ExampleEchoProcess
from task_handler.taskhandler import TaskHandler


class Window(QMainWindow):
    class MessageInfoSignal(QObject):
        signal = pyqtSignal(MessageInfo)

    def __init__(self):
        super().__init__()
        self.init_variables()
        self.init_UI()
        self.is_graph_uploaded = False
        self.distributed_system: DistributedSystem | None = None
        self.window.setAttribute(Qt.WA_TranslucentBackground)
        self.messages = []
        self.anims = []
        self.message_info_signal = Window.MessageInfoSignal()
        self.message_info_signal.signal.connect(self.create_qmessage)
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
        self.center = QPoint(self.window_width // 2, self.all_height // 2)

        self.radius = min(self.window_width // 2, self.all_height // 2) - 2 * self.ellipse_radius

        self.stopped = False
        self.animation_group = QParallelAnimationGroup()

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

    def create_qmessage(self, message_info: MessageInfo):
        qmessage = QMessage(
            message_info.get_sender_id(),
            message_info.get_receiver_id(),
            message_info.get_total_delay(),
        )
        qmessage.set_graph(self.vertexes)
        qmessage.set_size([self.window_width, self.all_height])
        self.add_message(qmessage)

    def create_new_delay_channel(self, sender_id, receiver_id, delay_range) -> MessageInfoDelayChannel:
        channel = MessageInfoDelayChannel(
            sender_id,
            receiver_id,
            delay_range,
            self.get_message_callback,
            None
        )
        return channel

    def get_message_callback(self, message_info: MessageInfo):
        self.message_info_signal.signal.emit(message_info)

    def file_menu_selected(self, q):

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
        # self.test()
        # self.start_test()
        distributed_system_builder = DistributedSystemBuilder() \
            .enable_one_thread_model(True) \
            .set_async_model(DistributedSystemBuilder.LooperType.QThread, 10)

        for i in range(len(data)):
            distributed_system_builder.add_process(
                ExampleEchoProcess(i, None, i == 0)
            )
            for j in range(len(data[i])):
                if i == j:
                    continue
                if data[i][j] == 1:
                    distributed_system_builder.add_channel(
                        self.create_new_delay_channel(
                            i,
                            j,
                            [7, 9]
                        ),
                        i,
                        j
                    )

        distributed_system_builder.check()

        self.distributed_system = distributed_system_builder.build()

        """
        for i in range(message_delay):
            if not self.stopped:
                self.update()
                QApplication.processEvents()
                """

        # timer = QTimer(self)
        # timer.setSingleShot(True)
        # self.layout().removeWidget(message)
        # Connect the timer's timeout signal to a function that will remove the widget
        # timer.timeout.connect(lambda : self.layout().removeWidget(message))

        # Start the timer with a 2 second delay
        # timer.start(4000)

        # self.paint_message_traversal(message_delay, 1, 2)

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
            # print("Timer pushed" + time.time().__str__())

    def paint_process(self, painter, x, y):
        painter.drawEllipse(x, y, self.ellipse_radius, self.ellipse_radius)

    def on_stop_click(self):
        if not self.stopped:
            self.distributed_system.unpause()
            self.stopped = True
            self.stop_algo.setText("Resume")
            for message in self.messages:
                message.stop()
            for anim in self.anims:
                anim.pause()
        else:
            self.stopped = False
            self.distributed_system.pause()
            self.stop_algo.setText("Stop")
            for message in self.messages:
                message.resume()
            for anim in self.anims:
                anim.resume()

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

        self.delivery_chance = QLineEdit(self)
        self.delivery_chance.move(20, 20)
        self.delivery_chance.resize(280, 40)
        self.delivery_chance.setFont(QFont("Arial", 16))
        self.delivery_chance.setText("1")
        self.delivery_chance.setReadOnly(True)

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
        self.regular_channel_type.setChecked(True)

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
        self.start_algo.clicked.connect(self.start_algorithm)

        self.stop_algo = QtWidgets.QPushButton("Stop")
        self.stop_algo.setFont(QFont("Arial", 18))
        self.stop_algo.setFixedSize(200, 50)
        self.stop_algo.clicked.connect(self.on_stop_click)

        self.execution = QtWidgets.QPushButton("Get execution")
        self.execution.setFont(QFont("Arial", 18))
        self.execution.setFixedSize(200, 50)
        self.execution.clicked.connect(self.get_execution)

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
        layout.addWidget(self.execution, 9, 0, 2, 0, Qt.AlignCenter)

        rect = QRect(self.all_width - self.menu_width, 0, self.menu_width, self.menu_height)

        self.menu = QWidget()
        self.menu.setLayout(layout)
        self.menu.setGeometry(rect)

        self.layout().addWidget(self.menu)

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

    def add_message(self, message: QMessage):
        print("************")
        print(f"Message added at time {time.time()} from {message.sender} to {message.recipient}")
        print("************")
        anim = message.build_animation()
        self.layout().addWidget(message)
        anim.finished.connect(lambda: self.remove_message(message, anim))
        # anim.setDuration(40000)
        self.anims.append(anim)
        anim.start()
        if self.stopped:
            anim.pause()
        """
        message.is_deleted.connect(lambda: self.remove_message(message))
        message.set_size([self.window_width, self.all_height])
        message.build_animation()
        self.messages.append(message)
        self.setUpdatesEnabled(False)
        self.layout().addWidget(message)
        self.setUpdatesEnabled(True)
        self.animation_group.addAnimation(message.get_animation())
        message.animate()
        """

    def start_algorithm(self):
        if self.distributed_system:
            self.distributed_system.start()

    def remove_message(self, message, anim):
        print("Message removed " + str(message))
        # self.messages.remove(message)
        self.layout().removeWidget(message)
        self.anims.remove(anim)
        anim.deleteLater()
        message.deleteLater()
        print("Messages: ")
        print(self.messages)

    def get_execution(self):
        self.on_stop_click()
        strings = ["first", "second", "third"]
        sub_window = QMainWindow(self)

        # Set the text edit widget as the central widget of the sub-window
        execution_log = QTextEdit(self)
        execution_log.clear()
        for log in self.distributed_system.get_execution_log():
            execution_log.append(log)
        sub_window.layout().addWidget(execution_log)

        sub_window.setCentralWidget(execution_log)
        execution_log.setFixedSize(400, 500)
        sub_window.setWindowTitle("Distributed executions log")
        sub_window.move(int(self.all_width / 2) - 200, int(self.all_height / 2) - 250)
        sub_window.setFixedSize(400, 500)
        sub_window.show()

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

    def test(self):
        for j in range(70):
            message = QMessage(randint(0, 3), randint(0, 3), 5)
            message.set_size([self.window_width, self.all_height])
            message.set_graph(self.vertexes)
            self.add_message(message)

    def start_test(self):
        for anim in self.anims:
            anim.start()


def application_start():
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())
