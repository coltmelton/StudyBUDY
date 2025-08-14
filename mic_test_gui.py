#Test if my laptop is bugging
import sys
import numpy as np
import pyaudio
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

class MicTestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mic Test")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.mic_label = QLabel("Mic Volume: 0")
        self.layout.addWidget(self.mic_label)

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,channels=CHANNELS,rate=RATE,input=True,frames_per_buffer=CHUNK)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_mic_level)
        self.timer.start(50)

    def update_mic_level(self):
        data = np.frombuffer(self.stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        volume = int(np.abs(data).mean())
        self.mic_label.setText(f"Mic Volume: {volume}")

    def closeEvent(self, event):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MicTestApp()
    window.show()
    sys.exit(app.exec())
