from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QScrollArea, QGridLayout
from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter, QBrush, QPalette, QLinearGradient, QPen
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
import os
import sys
import subprocess
import json



class FileExplorer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.file_paths = []
        self.custom_images = {}  # Add this line
        self.load_file_paths()

    def initUI(self):
        # Set background gradient from green to black
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, 400)
        gradient.setColorAt(0.0, QColor(0, 128, 0))
        gradient.setColorAt(1.0, QColor(0, 0, 0))
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        self.layout = QVBoxLayout()
        self.select_file_button = QPushButton("ADD")
        self.select_file_button.clicked.connect(self.select_file)
        self.layout.addWidget(self.select_file_button)
        self.scroll_area = QScrollArea()
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

    def select_file(self):
        file_paths = QFileDialog.getOpenFileNames(self, "Select Files")[0]
        if file_paths:
            self.file_paths.extend(file_paths)
            self.save_file_paths()
            self.display_images()


    def display_images(self):
        grid_layout = QGridLayout()
        for i, file_path in enumerate(self.file_paths):
            if file_path in self.custom_images:
                pixmap = QPixmap(self.custom_images[file_path])
            elif os.path.isfile(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                pixmap = QPixmap(file_path)
            else:
                # Display placeholder image for non-image files
                pixmap = QPixmap('image.png')
            pixmap = self.center_crop(pixmap)
            pixmap = pixmap.scaled(150, 225, Qt.KeepAspectRatio)
            label = ClickableLabel(file_path, pixmap)
            label.setPixmap(pixmap)
            label.setFixedSize(150, 225)  # Set fixed size for QLabel
            label.clicked.connect(self.on_image_click)
            label.rightClicked.connect(self.add_custom_image)
            label.middleClicked.connect(self.delete_file)  # Add this line
            grid_layout.addWidget(label, i // 5, i % 5)  # Adjust number of columns in QGridLayout
        widget = QWidget()
        widget.setLayout(grid_layout)
        self.scroll_area.setWidget(widget)

    def delete_file(self, file_path):
        if file_path in self.file_paths:
            self.file_paths.remove(file_path)
        if file_path in self.custom_images:
            del self.custom_images[file_path]
        self.save_file_paths()
        self.display_images()
        
    def on_image_click(self, file_path):
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', file_path))
        elif os.name == 'nt':  # For Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # For Linux, Mac, etc.
            subprocess.call(('xdg-open', file_path))

    def add_custom_image(self, label):
        custom_image_path = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.gif)")[0]
        if custom_image_path:
            pixmap = QPixmap(custom_image_path)
            pixmap = self.center_crop(pixmap)
            pixmap = pixmap.scaled(200, 300, Qt.KeepAspectRatio)
            label.setPixmap(pixmap)
            label.update()
            self.custom_images[label.file_path] = custom_image_path  # Add this line
            self.save_file_paths()  # Save the file paths and custom images
            



    def center_crop(self, pixmap):
        image = pixmap.toImage()
        width = image.width()
        height = image.height()
        new_width = min(width, height * 2 / 3)
        new_height = min(height, width * 3 / 2)
        x = (width - new_width) / 2
        y = (height - new_height) / 2
        image = image.copy(int(x), int(y), int(new_width), int(new_height))
        return QPixmap.fromImage(image)

    def save_file_paths(self):
        with open('file_paths.json', 'w') as f:
            json.dump({'file_paths': self.file_paths, 'custom_images': self.custom_images}, f)

    def load_file_paths(self):
        if os.path.exists('file_paths.json'):
            with open('file_paths.json', 'r') as f:
                data = json.load(f)
                if isinstance(data, list):  # Old format
                    self.file_paths = data
                    
                else:  # New format
                    self.file_paths = data['file_paths']
                    self.custom_images = data['custom_images']
            self.display_images()




class ClickableLabel(QLabel):
    clicked = pyqtSignal(str)
    rightClicked = pyqtSignal(QLabel)
    middleClicked = pyqtSignal(str)

    def __init__(self, file_path, pixmap, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.pixmap = pixmap
        self.installEventFilter(self)
        self.hover = False

    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.Enter:
                self.hover = True
                self.update()
            elif event.type() == QEvent.Leave:
                self.hover = False
                self.update()
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)  # Draw pixmap first
        if self.hover:
            painter.setPen(QPen(QColor(0, 0, 255, 127), 10))  # Set pen for border
            painter.drawRect(self.rect().adjusted(5, 5, -5, -5))  # Draw border outside the image

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.file_path)
        elif event.button() == Qt.RightButton:
            self.rightClicked.emit(self)
        elif event.button() == Qt.MiddleButton:  # Add these lines
            self.middleClicked.emit(self.file_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = FileExplorer()
    ex.showMaximized()  # Open the application maximized
    sys.exit(app.exec_())
