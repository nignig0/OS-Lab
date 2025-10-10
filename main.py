import sys
import threading
import time
from PyQt6.QtCore import QTimer, Qt, QRect, QPointF
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGridLayout, QSizePolicy, QScrollArea
from PyQt6.QtGui import QFont, QPainter, QColor, QLinearGradient, QBrush

from classes import MemoryBlock
from constants import MEMORY_LIST, JOBLIST
from first_fit import first_fit


class GradientProgressBar(QWidget):
    """
    gradient progress bar showing used and fragmented memory.
    """
    def __init__(self, max_value):
        super().__init__()
        self.max_value = max_value
        self.job_value = 0
        self.fragmentation_value = 0
        self.setMinimumHeight(35)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def setValues(self, job_value, fragmentation_value):
        self.job_value = job_value
        self.fragmentation_value = fragmentation_value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        # Background (dark grey)
        painter.setBrush(QColor("#333333"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 12, 12)

        width = rect.width()
        height = rect.height()

        if self.max_value == 0:
            return

        job_width = int((self.job_value / self.max_value) * width)
        frag_width = int((self.fragmentation_value / self.max_value) * width)

        # Draw job portion with green gradient
        if job_width > 0:
            grad = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.topRight()))
            grad.setColorAt(0, QColor("#56ab2f"))
            grad.setColorAt(1, QColor("#a8e063"))
            painter.setBrush(QBrush(grad))
            job_rect = QRect(rect.x(), rect.y(), job_width, height)
            painter.drawRoundedRect(job_rect, 12, 12)

        # Draw fragmentation portion with orange gradient
        if frag_width > 0:
            grad = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.topRight()))
            grad.setColorAt(0, QColor("#f7971e"))
            grad.setColorAt(1, QColor("#ffd200"))
            painter.setBrush(QBrush(grad))
            frag_rect = QRect(rect.x() + job_width, rect.y(), frag_width, height)
            painter.drawRect(frag_rect)

        # Draw sleek border
        painter.setPen(QColor("#4caf50"))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 12, 12)


class MemoryBlockWidget(QWidget):
    def __init__(self, block: MemoryBlock):
        super().__init__()
        self.block = block

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        self.setLayout(self.layout)

        # Block index with shadow and bold font
        self.label_index = QLabel(f"Block #{block.index}")
        self.label_index.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.label_index.setStyleSheet("""
            color: #2e7d32;
        """)
        self.layout.addWidget(self.label_index, alignment=Qt.AlignmentFlag.AlignCenter)

        # Block size label smaller and lighter
        self.label_block_size = QLabel(f"Total Size: {block.space}")
        self.label_block_size.setFont(QFont("Segoe UI", 12))
        self.label_block_size.setStyleSheet("color: #7a7a7a;")
        self.layout.addWidget(self.label_block_size, alignment=Qt.AlignmentFlag.AlignCenter)

        # Gradient progress bar
        self.progress_bar = GradientProgressBar(block.space)
        self.layout.addWidget(self.progress_bar)

        # Info label with multi-line and modern font
        self.label_info = QLabel("Free")
        self.label_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_info.setWordWrap(True)
        self.label_info.setFont(QFont("Segoe UI", 13))
        self.label_info.setStyleSheet("color: #444444;")
        self.layout.addWidget(self.label_info)

        self.layout.addStretch()

        # Job timing tracking
        self.job_start_time = None
        self.job_duration = None
        self.draining = False
        self.drain_duration = 1.8
        self.drain_start_time = None

        # Modern card style with drop shadow and radius
        self.setStyleSheet("""
            MemoryBlockWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e0f2f1, stop:1 #a7ffeb);
                border-radius: 20px;
                border: 2px solid #00796b;
            }
        """)
        self.setFixedSize(220, 300)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def update_status(self):
        job_num = self.block.job_in_progress

        if job_num is None and not self.draining:
            self.progress_bar.setValues(0, 0)
            self.label_info.setText("Free")
            self.job_start_time = None
            self.job_duration = None
            return

        if job_num is not None and self.job_start_time is None:
            self.job_start_time = time.monotonic()
            job = JOBLIST[job_num - 1]
            self.job_duration = job.time
            self.draining = False

        if job_num is not None and not self.draining:
            elapsed = time.monotonic() - self.job_start_time
            job = JOBLIST[job_num - 1]

            progress = min(elapsed / self.job_duration, 1.0) * job.size
            fragmentation = self.block.space - job.size

            self.progress_bar.setValues(int(progress), fragmentation)

            frag_text = f"<span style='color:#ff6f00;'>Fragmentation: {fragmentation}</span>" if fragmentation > 0 else ""
            self.label_info.setText(
                f"<b>Job #{job_num}</b><br>Size: {job.size}<br>{frag_text}"
            )

            if elapsed >= self.job_duration:
                self.draining = True
                self.drain_start_time = time.monotonic()

        elif self.draining:
            elapsed_drain = time.monotonic() - self.drain_start_time
            job = JOBLIST[job_num - 1] if job_num else None
            start_val = job.size if job else self.progress_bar.job_value
            drain_progress = max(1.0 - (elapsed_drain / self.drain_duration), 0)
            value = int(start_val * drain_progress)
            fragmentation = self.block.space - job.size if job else 0
            self.progress_bar.setValues(value, fragmentation)

            self.label_info.setText("Free" if value == 0 else self.label_info.text())

            if value == 0:
                self.draining = False
                self.job_start_time = None
                self.job_duration = None


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Memory Blocks Job Allocation")
        self.resize(1200, 800)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(20)
        self.setLayout(self.main_layout)

        self.title_label = QLabel("Memory Blocks Job Allocation Visualization")
        self.title_label.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            color: #00796b;
        """)
        self.main_layout.addWidget(self.title_label)

        # Scroll area (vertical + horizontal) so all blocks fit in grid nicely
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.main_layout.addWidget(self.scroll_area, 1)  # Stretch factor 1 fills space

        container = QWidget()
        self.scroll_area.setWidget(container)

        # Use grid layout for blocks (adjust rows/cols automatically)
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(30)
        container.setLayout(self.grid_layout)

        # Dynamically compute rows and cols for balanced grid
        num_blocks = len(MEMORY_LIST)
        cols = 4  # fixed columns to create a neat grid
        rows = (num_blocks + cols - 1) // cols

        self.block_widgets = []
        for i, block in enumerate(MEMORY_LIST):
            w = MemoryBlockWidget(block)
            self.block_widgets.append(w)
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(w, row, col)

        self.lock = threading.Lock()

        self.thread = threading.Thread(target=first_fit, args=(self.lock,), daemon=True)
        self.thread.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(100)

        self.setStyleSheet("""
            QWidget {
                background-color: #e0f7fa;
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            }
            QLabel {
                font-size: 12pt;
            }
        """)

    def update_ui(self):
        with self.lock:
            for widget in self.block_widgets:
                widget.update_status()


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
