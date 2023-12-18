import sys
from PyQt5.QtWidgets import QPushButton, QHBoxLayout,QVBoxLayout, QApplication, QToolTip, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QMainWindow, QWidget, QLabel, QComboBox, QFileDialog
from PyQt5.QtGui import QPixmap, QImage, QTransform, QPainter, QPen, QCursor
from PyQt5.QtCore import Qt, QSize

import fitz  # PyMuPDF

class ImageViewer(QMainWindow):
    def __init__(self):
        super(ImageViewer, self).__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Viewer')

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Horizontal layout for origin dropdown and "Select File" button
        origin_file_layout = QHBoxLayout()
        
        # Add a title for the set origin dropdown
        origin_title_label = QLabel("Set Origin:", self)

        # Dropdown menu for selecting the origin
        self.origin_dropdown = QComboBox(self)
        self.origin_dropdown.addItem("Top Left")
        self.origin_dropdown.addItem("Bottom Left")
        self.origin_dropdown.addItem("Top Right")
        self.origin_dropdown.addItem("Bottom Right")
        self.origin_dropdown.currentIndexChanged.connect(self.set_selected_origin)
        

        # Button to open a file dialog for image or PDF selection
        self.open_file_button = QPushButton("Select File", self)
        self.open_file_button.clicked.connect(self.open_file_dialog)
        origin_file_layout.addWidget(self.open_file_button, alignment=Qt.AlignLeft)
        origin_file_layout.addWidget(origin_title_label, alignment=Qt.AlignLeft)
        origin_file_layout.addWidget(self.origin_dropdown,stretch=1, alignment=Qt.AlignLeft)

        self.layout.addLayout(origin_file_layout)


        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.layout.addWidget(self.view)

        self.image_item = QGraphicsPixmapItem()
        self.scene.addItem(self.image_item)

        self.origin = Qt.TopLeftCorner
        self.zoom_factor = 1.0

        self.view.mouseMoveEvent = self.mouseMoveEvent
        self.view.mousePressEvent = self.mousePressEvent
        self.view.mouseReleaseEvent = self.mouseReleaseEvent
        self.view.wheelEvent = self.wheelEvent

        self.panning = False
        self.Coord_flag = None

        # QLabel to display mouse coordinates
        self.coordinates_label = QLabel(self)
        self.layout.addWidget(self.coordinates_label)

        # Set dark theme stylesheet
        self.set_stylesheet()

    def set_stylesheet(self):
        style_sheet = """
            QComboBox {
                max-width: 100px;  /* Set the minimum width for QComboBox */
            }
            QPushButton {
                max-width: 100px;
            }
            """
        self.setStyleSheet(style_sheet)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Image Files (*.png *.jpg *.jpeg *.bmp);;PDF Files (*.pdf);;All Files (*)", options=options)
        if file_path:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.open_image(file_path)
            elif file_path.lower().endswith('.pdf'):
                self.open_pdf(file_path)

    def open_image(self, file_path):
        self.Coord_flag = "Image"
        pixmap = QPixmap(file_path)

        # Add a border around the image
        border_color = Qt.red  # You can change the color if needed
        border_width = 2
        pixmap_with_border = QPixmap(pixmap.size() + QSize(2 * border_width, 2 * border_width))
        pixmap_with_border.fill(Qt.red)
        painter = QPainter(pixmap_with_border)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(border_color, border_width))
        painter.drawPixmap(border_width, border_width, pixmap)
        painter.end()

        self.image_item.setPixmap(pixmap_with_border)

        # Get the center position of the view
        center_pos = self.view.mapToScene(self.view.viewport().rect().center())
        # Trigger the initial mouse move event
        self.show_coordinates(center_pos)

    def open_pdf(self, file_path):
        self.Coord_flag = "Pdf"
        doc = fitz.open(file_path)
        pixmap_list = []
        zoom_factor = 2.0  # Adjust this value as needed for better quality

        for page_num in range(doc.page_count):
            page = doc[page_num]
            img = page.get_pixmap(matrix=fitz.Matrix(zoom_factor, zoom_factor))
            pixmap = QPixmap.fromImage(QImage(img.samples, img.width, img.height, img.stride, QImage.Format_RGB888))

            # Add a border around the image
            border_color = Qt.red  # You can change the color if needed
            border_width = 2
            pixmap_with_border = QPixmap(pixmap.size() + QSize(2 * border_width, 2 * border_width))
            pixmap_with_border.fill(Qt.red)
            painter = QPainter(pixmap_with_border)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(border_color, border_width))
            painter.drawPixmap(border_width, border_width, pixmap)
            painter.end()

            pixmap_list.append(pixmap_with_border)

        doc.close()

        self.image_item.setPixmap(pixmap_list[0])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:  # Check for middle button (scroll wheel) press
            self.panning = True
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.panning:
            delta = event.pos() - self.last_mouse_pos
            self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().value() - delta.x())
            self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().value() - delta.y())
            self.last_mouse_pos = event.pos()
        scene_pos = self.view.mapToScene(event.pos())
        self.show_coordinates(scene_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.panning = False

    def wheelEvent(self, event):
        zoom_factor = 1.2
        mouse_pos = event.pos()
        zoom_point = self.view.mapToScene(mouse_pos)

        if event.angleDelta().y() > 0:
            self.zoom_factor *= zoom_factor
        else:
            self.zoom_factor /= zoom_factor

        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.resetTransform()
        self.view.scale(self.zoom_factor, self.zoom_factor)
        self.view.centerOn(zoom_point)

    def set_origin(self, origin):
        self.origin = origin

    def set_selected_origin(self):
        selected_index = self.origin_dropdown.currentIndex()
        if selected_index == 0:
            self.set_origin(Qt.TopLeftCorner)
        elif selected_index == 1:
            self.set_origin(Qt.BottomLeftCorner)
        elif selected_index == 2:
            self.set_origin(Qt.TopRightCorner)
        elif selected_index == 3:
            self.set_origin(Qt.BottomRightCorner)

        # Update the coordinates label based on the new origin
        if hasattr(self, 'last_mouse_pos'):
            scene_pos = self.view.mapToScene(self.last_mouse_pos)
            self.show_coordinates(scene_pos)

    def show_coordinates(self, scene_pos):
        image_rect = self.image_item.pixmap().rect()
        image_width = image_rect.width()
        image_height = image_rect.height()

        if self.origin == Qt.TopLeftCorner:
            x = scene_pos.x()
            y = scene_pos.y()
        elif self.origin == Qt.BottomLeftCorner:
            x = scene_pos.x()
            y = image_height - scene_pos.y()
        elif self.origin == Qt.TopRightCorner:
            x = image_width - scene_pos.x()
            y = scene_pos.y()
        elif self.origin == Qt.BottomRightCorner:
            x = image_width - scene_pos.x()
            y = image_height - scene_pos.y()

        if self.Coord_flag == "Pdf":
            coordinates_text = f'Co-Ordinates: (X={int(x // 2)} Y={int(y // 2)})'
        else:
            coordinates_text = f'Co-Ordinates: (X={int(x)} Y={int(y)})'

        self.coordinates_label.setText(coordinates_text)

        # Get global cursor position
        cursor_pos = QCursor.pos()

        # Set the tooltip text at the cursor position
        QToolTip.showText(cursor_pos, coordinates_text, self)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.setGeometry(100, 100, 800, 600)

    viewer.show()
    sys.exit(app.exec_())
