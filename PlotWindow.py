
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class PlotWindow(QtWidgets.QFrame):


    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent)

        self.figure = Figure(tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = self.figure.add_subplot(111)
        self.setWindowTitle('Plot window')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.resize(800,500)


    def drawSafe(self):
        try:
            self.canvas.draw()
        except RuntimeError as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(e.strerror)
            msg.setWindowTitle('Runtime Error')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()


    def plot(self, *args, **kwargs):
        self.ax.plot(*args, **kwargs)


    def set_xlabel(self, *args, **kwargs):
        self.ax.set_xlabel(*args, **kwargs)


    def set_ylabel(self, *args, **kwargs):
        self.ax.set_ylabel(*args, **kwargs)


