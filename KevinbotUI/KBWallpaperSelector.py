import os
import subprocess

from qtpy.QtCore import QSize, Qt, Signal
from qtpy.QtGui import QPixmap, QCursor, QPalette, QColor
from qtpy.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QMenu,
    QAction,
    QFrame,
)


def get_scaled_pixmap(image_path):
    pixmap = QPixmap(image_path)
    return pixmap.scaled(
        QSize(200, 100),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


class WallpaperCarousel(QWidget):
    selected = Signal(str, name="WallpaperSelect")

    def __init__(self, directory):
        super().__init__()

        # Initialize main layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Initialize the scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Initialize the widget to hold the wallpapers
        self.wallpaper_container = QWidget()
        self.wallpaper_layout = QGridLayout(self.wallpaper_container)
        self.wallpaper_container.setLayout(self.wallpaper_layout)

        # Track selected label
        self.selected_label = None

        # Store wallpaper labels
        self.wallpaper_labels = []

        # Load wallpapers
        self.load_wallpapers(directory)

        # Set the container widget for the scroll area
        self.scroll_area.setWidget(self.wallpaper_container)
        self.layout.addWidget(self.scroll_area)

        # Connect the resize event to adjust the layout
        self.scroll_area.resizeEvent = self.adjust_grid_layout

    def load_wallpapers(self, wallpaper_dir):
        for filename in os.listdir(wallpaper_dir):
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                full_path = os.path.join(wallpaper_dir, filename)
                wallpaper_label = self.create_wallpaper_label(full_path)
                self.wallpaper_labels.append(wallpaper_label)
                self.wallpaper_layout.addWidget(
                    wallpaper_label, 0, len(self.wallpaper_labels) - 1
                )

    def create_wallpaper_label(self, image_path):
        label = WallpaperLabel(image_path)
        label.setPixmap(get_scaled_pixmap(image_path))
        label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        label.customContextMenuRequested.connect(self.show_context_menu)
        label.mouseDoubleClickEvent = lambda event: self.select_wallpaper(label)
        return label

    def adjust_grid_layout(self, event):
        if not self.wallpaper_labels:
            return

        available_width = self.scroll_area.width()
        label_width = self.wallpaper_labels[0].sizeHint().width()
        num_columns = max(1, available_width // label_width)

        # Clear the layout
        for i in reversed(range(self.wallpaper_layout.count())):
            widget = self.wallpaper_layout.itemAt(i).widget()
            if widget:
                self.wallpaper_layout.removeWidget(widget)

        # Re-add the labels in the grid layout
        for index, label in enumerate(self.wallpaper_labels):
            row = index // num_columns
            column = index % num_columns
            self.wallpaper_layout.addWidget(label, row, column)

        event.accept()

    def select_wallpaper(self, label):
        if self.selected_label:
            self.selected_label.set_highlight(False)

        self.selected_label = label
        self.selected_label.set_highlight(True)

        self.selected.emit(self.selected_label.image_path)

    def show_context_menu(self):
        label = self.sender()
        image_path = label.image_path

        menu = QMenu(self)

        select_action = QAction("Select", self)
        select_action.triggered.connect(lambda: self.select_wallpaper(label))
        menu.addAction(select_action)

        view_action = QAction("View", self)
        view_action.triggered.connect(lambda: self.view_wallpaper(image_path))
        menu.addAction(view_action)

        menu.exec(QCursor.pos())

    def view_wallpaper(self, image_path):
        try:
            subprocess.run(["xdg-open", image_path], check=True)
        except Exception as e:
            print(f"Failed to open image: {e}")

    def select_wallpaper(self, label):
        self.selected.emit(label.image_path)


class WallpaperLabel(QLabel):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setFrameShape(QFrame.Shape.Box)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.set_highlight(False)

    def set_highlight(self, highlight):
        if highlight:
            self.setLineWidth(0)
            self.setFrameShadow(QFrame.Shadow.Plain)
            self.setPalette(self.palette().highlight().color())
            self.setAutoFillBackground(True)
        else:
            self.setLineWidth(0)
            self.setFrameShadow(QFrame.Shadow.Plain)
            self.setPalette(QPalette(QColor(0, 0, 0)))
            self.setAutoFillBackground(False)

    def focusInEvent(self, event):
        self.set_highlight(True)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.set_highlight(False)
        super().focusOutEvent(event)
