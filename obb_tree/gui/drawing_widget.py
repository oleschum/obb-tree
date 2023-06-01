from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget


class DrawingWidget(QWidget):
    def __init__(self, w, h, parent=None):
        super().__init__(parent)
        self.setFixedSize(w, h)
        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.image.fill(Qt.white)
        self.drawing = False
        self.previous_point = None
        self.brush_size = 5
        self.brush_color = Qt.black
        self.eraser_color = Qt.white

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.image, self.image.rect())
        painter.end()

    def resizeEvent(self, event):
        scaled_image = self.image.scaled(event.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image = QImage(event.size(), QImage.Format_RGB32)
        self.image.fill(Qt.white)
        painter = QPainter(self.image)
        painter.drawImage((self.image.width() - scaled_image.width()) / 2,
                          (self.image.height() - scaled_image.height()) / 2, scaled_image)
        painter.end()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.draw_point(event.position())

    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton and self.drawing:
            if self.previous_point:
                self.draw_line(self.previous_point, event.position())
            else:
                self.draw_point(event.position())
            self.previous_point = event.position()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            self.previous_point = None

    def draw_point(self, pos):
        self._draw(pos, self.brush_color)

    def erase_point(self, pos):
        self._draw(pos, self.eraser_color)

    def _draw(self, pos, color):
        painter = QPainter(self.image)
        painter.setPen(QPen(color, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        scaling_factor = self.image.width() / self.width()
        scaled_pos = pos * scaling_factor
        painter.drawPoint(scaled_pos)
        painter.end()
        self.update()

    def draw_line(self, p1, p2):
        painter = QPainter(self.image)
        painter.setPen(QPen(self.brush_color, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        scaling_factor = self.image.width() / self.width()
        scaled_p1 = p1 * scaling_factor
        scaled_p2 = p2 * scaling_factor

        painter.drawLine(scaled_p1, scaled_p2)
        painter.end()
        self.update()

    def clear(self):
        self.image.fill(Qt.white)
        self.update()
