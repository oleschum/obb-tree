import sys
import numpy as np

from PySide6.QtCore import Qt, QPoint, QRect, QPointF
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QPixmap, QPolygonF
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSpinBox, \
    QPushButton, QGraphicsPixmapItem, QGraphicsScene, QGraphicsPolygonItem, QCheckBox, QFormLayout
from skimage import measure

from obb_tree.gui.drawing_widget import DrawingWidget
from obb_tree.gui.zoom_pan_graphicsview import ZoomableGraphicsView
from obb_tree.obb import get_indices_for_segment, create_obb_tree
from obb_tree.segment_count import count_pixels_per_segment


class ResultScene(QGraphicsScene):

    def __init__(self, parent=None):
        super(ResultScene, self).__init__(parent)
        self._obb_rects = []  # type: list[QGraphicsPixmapItem]
        self._ccl_image_item = None
        self.colors = [
            QColor(0, 114, 189),  # Blue
            QColor(217, 83, 25),  # Orange
            QColor(237, 177, 32),  # Yellow
            QColor(126, 47, 142),  # Purple
            QColor(119, 172, 48),  # Green
            QColor(77, 190, 238),  # Light blue
            QColor(162, 20, 47),  # Red
            QColor(255, 157, 0),  # Orange-yellow
            QColor(164, 196, 0),  # Lime green
            QColor(153, 153, 153),  # Gray
        ]

    def remove_obbs(self):
        for item in self._obb_rects:
            self.removeItem(item)
        self._obb_rects = []

    def draw_obb(self, obb):
        corners = obb.corners[:, ::-1]
        corners = [QPointF(x[0], x[1]) for x in corners]
        polygon = QPolygonF(corners)
        polygon_item = QGraphicsPolygonItem(polygon)
        depth = 0 if obb.depth is None else obb.depth
        pen = QPen(self.colors[depth % len(self.colors)])
        pen.setWidth(2)
        pen.setCosmetic(True)
        pen.setStyle(Qt.DotLine)
        polygon_item.setPen(pen)

        self.addItem(polygon_item)
        self._obb_rects.append(polygon_item)

    def draw_ccl_image(self, image, labels):
        if self._ccl_image_item is not None:
            self.removeItem(self._ccl_image_item)

        component_image = QImage(image.size(), QImage.Format_RGB32)
        component_image.fill(Qt.white)
        painter = QPainter(component_image)
        for i in range(image.width()):
            for j in range(image.height()):
                if labels[j, i] > 0:
                    painter.fillRect(QRect(i, j, 1, 1), self.colors[(labels[j, i] - 1) % len(self.colors)])
        painter.end()
        self._ccl_image_item = self.addPixmap(QPixmap.fromImage(component_image))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        im_w, im_h = 512, 512
        self.drawing_widget = DrawingWidget(im_w, im_h)

        self.result_view = ZoomableGraphicsView()
        self.result_view.setFixedSize(im_w + 10, im_h + 10)
        self.result_scene = ResultScene(self)
        self.result_view.setScene(self.result_scene)

        self.ccl_result = None

        self.brush_size_spinbox = QSpinBox()
        self.brush_size_spinbox.setRange(1, 30)
        self.brush_size_spinbox.setValue(5)
        self.brush_size_spinbox.valueChanged.connect(self.on_brush_size_changed)

        self.drawing_button = QPushButton("Draw")
        self.drawing_button.setCheckable(True)
        self.drawing_button.setChecked(True)
        self.drawing_button.clicked.connect(self.on_drawing_button_clicked)

        self.eraser_button = QPushButton("Erase")
        self.eraser_button.setCheckable(True)
        self.eraser_button.clicked.connect(self.on_eraser_button_clicked)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.on_clear_button_clicked)

        self.connected_component_button = QPushButton("Connected Component Analysis")
        self.connected_component_button.clicked.connect(self.on_connected_component_button_clicked)

        self.obbs_button = QPushButton("Oriented Bounding Boxes")
        self.obbs_button.clicked.connect(self.on_obbs_button_clicked)

        recursion_depth_label = QLabel("Max OBB Tree Depth:")
        self.recursion_depth_spinbox = QSpinBox()
        self.recursion_depth_spinbox.setRange(0, 10)
        self.recursion_depth_spinbox.setValue(3)
        self.recursion_depth_spinbox.valueChanged.connect(self.on_obbs_button_clicked)

        draw_level_label = QLabel("Draw Only Level:")
        self.draw_level_spinbox = QSpinBox()
        self.draw_level_spinbox.setRange(0, 10)
        self.draw_level_spinbox.setValue(2)
        self.draw_level_spinbox.valueChanged.connect(self.on_obbs_button_clicked)

        self.draw_all_obbs_checkbox = QCheckBox("Draw all OBBs")
        self.draw_all_obbs_checkbox.stateChanged.connect(self.on_draw_all_obbs_checkbox_stateChanged)
        self.draw_all_obbs_checkbox.stateChanged.connect(self.on_obbs_button_clicked)
        self.draw_all_obbs_checkbox.setChecked(True)

        obbs_layout = QFormLayout()
        obbs_layout.addRow(self.obbs_button)
        obbs_layout.addRow(recursion_depth_label, self.recursion_depth_spinbox)
        obbs_layout.addRow(draw_level_label, self.draw_level_spinbox)
        obbs_layout.addRow(self.draw_all_obbs_checkbox)

        config_layout = QVBoxLayout()
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Brush Size"))
        hlayout.addWidget(self.brush_size_spinbox)
        config_layout.addLayout(hlayout)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.drawing_button)
        hlayout.addWidget(self.eraser_button)
        hlayout.addWidget(self.clear_button)
        config_layout.addLayout(hlayout)
        config_layout.addWidget(self.connected_component_button)
        config_layout.addLayout(obbs_layout)

        self.ccl_image_label = QLabel()
        self.ccl_image_label.setFixedSize(im_w, im_h)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.drawing_widget)
        main_layout.addLayout(config_layout)
        main_layout.addWidget(self.result_view)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setWindowTitle("OBB-Tree Visu Tool")

    def on_brush_size_changed(self, value):
        self.drawing_widget.brush_size = value

    def on_drawing_button_clicked(self, checked):
        if checked:
            self.drawing_widget.brush_color = Qt.black
            self.eraser_button.setChecked(False)

    def on_eraser_button_clicked(self, checked):
        if checked:
            self.drawing_widget.brush_color = Qt.white
            self.drawing_button.setChecked(False)

    def on_clear_button_clicked(self):
        self.drawing_widget.clear()

    def on_draw_all_obbs_checkbox_stateChanged(self, state):
        if self.draw_all_obbs_checkbox.isChecked():
            self.draw_level_spinbox.setEnabled(False)
        else:
            self.draw_level_spinbox.setEnabled(True)

    def on_obbs_button_clicked(self):
        if self.ccl_result is None:
            return
        self.result_view.obb_rects = []
        segment_counts, num_segments = count_pixels_per_segment(self.ccl_result.copy())
        self.result_scene.remove_obbs()
        draw_level = self.draw_level_spinbox.value()
        draw_all_obbs = self.draw_all_obbs_checkbox.isChecked()
        max_depth = self.recursion_depth_spinbox.value()
        for i in range(num_segments - 1):
            indices = get_indices_for_segment(self.ccl_result, i + 1)
            root, sub_trees = create_obb_tree(indices, max_depth=max_depth)

            if draw_all_obbs or root.depth == draw_level:
                self.result_scene.draw_obb(root)

            def traverse_tree(tree):
                if len(tree) > 0:
                    for obb, sub_t in tree:
                        depth = obb.depth
                        if draw_all_obbs or depth == draw_level:
                            self.result_scene.draw_obb(obb)
                        traverse_tree(sub_t)

            traverse_tree(sub_trees)

    def on_connected_component_button_clicked(self):
        image = self.drawing_widget.image
        gray_image = QImage(image.size(), QImage.Format_Grayscale8)
        painter = QPainter(gray_image)
        painter.drawImage(QPoint(0, 0), image)
        painter.end()

        array = np.frombuffer(gray_image.bits(), dtype=np.uint8).reshape((image.height(), image.width()))
        labels = measure.label(array, background=255, connectivity=2).astype(np.int32)
        self.ccl_result = labels
        self.result_scene.draw_ccl_image(self.drawing_widget.image, labels)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
