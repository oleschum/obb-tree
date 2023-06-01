from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setRenderHint(QPainter.Antialiasing)

        # Set the transformation anchor to the center of the view
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        # Set the view to track mouse events
        self.setMouseTracking(True)

        # Initialize the pan variables
        self.pan_start = QPointF(0, 0)
        self.pan_delta = QPointF(0, 0)

    def wheelEvent(self, event):
        # Set the zoom factor and limit the scale factor to reasonable values
        zoom_factor = 1.25
        zoom_in_limit = 100
        zoom_out_limit = 1

        # Scale the view by the zoom factor
        if event.angleDelta().y() > 0:
            # Zoom in
            if self.transform().m11() < zoom_in_limit:
                self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom out
            if self.transform().m11() > zoom_out_limit:
                self.scale(1 / zoom_factor, 1 / zoom_factor)

    def mousePressEvent(self, event):
        # Start panning the view when the left mouse button is pressed
        if event.button() == Qt.LeftButton:
            self.pan_start = event.position()
            self.pan_delta = QPointF(0, 0)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Pan the view when the left mouse button is held down
        if event.buttons() == Qt.LeftButton:
            delta = event.position() - self.pan_start
            if delta.x() != 0 or delta.y() != 0:
                self.pan_delta += delta
                self.translate(delta.x(), delta.y())
                self.pan_start = event.position()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)