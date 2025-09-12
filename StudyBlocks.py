# pip install ics
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDateEdit, QSpinBox, QTimeEdit,
    QDialogButtonBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import QDate, QTime

from ics import Calendar, Event

LOCAL_TZ = ZoneInfo("America/Detroit")  # adjust if needed

class StudyBlocksDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Study Blocks")
        form = QFormLayout(self)

        self.title = QLineEdit(self); self.title.setText("Study Block")
        self.start_date = QDateEdit(self); self.start_date.setDate(QDate.currentDate()); self.start_date.setCalendarPopup(True)
        self.days = QSpinBox(self); self.days.setRange(1, 30); self.days.setValue(5)
        self.blocks_per_day = QSpinBox(self); self.blocks_per_day.setRange(1, 10); self.blocks_per_day.setValue(3)
        self.block_minutes = QSpinBox(self); self.block_minutes.setRange(15, 240); self.block_minutes.setValue(50)
        self.day_start = QTimeEdit(self); self.day_start.setTime(QTime(18, 0))
        self.gap_minutes = QSpinBox(self); self.gap_minutes.setRange(0, 120); self.gap_minutes.setValue(10)

        form.addRow("Event title:", self.title)
        form.addRow("Start date:", self.start_date)
        form.addRow("Number of days:", self.days)
        form.addRow("Blocks per day:", self.blocks_per_day)
        form.addRow("Block length (min):", self.block_minutes)
        form.addRow("Daily start time:", self.day_start)
        form.addRow("Gap between blocks (min):", self.gap_minutes)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

def create_study_blocks(parent=None):
    dlg = StudyBlocksDialog(parent)
    if dlg.exec() != QDialog.Accepted:
        return

    title = dlg.title.text().strip() or "Study Block"
    start_qdate = dlg.start_date.date()
    days = dlg.days.value()
    blocks_per_day = dlg.blocks_per_day.value()
    block_min = dlg.block_minutes.value()
    gap_min = dlg.gap_minutes.value()
    day_start_qtime = dlg.day_start.time()

    c = Calendar()
    for day_offset in range(days):
        d = start_qdate.addDays(day_offset)
        start_dt = datetime(d.year(), d.month(), d.day(),
                            day_start_qtime.hour(), day_start_qtime.minute(),
                            tzinfo=LOCAL_TZ)

        for b in range(blocks_per_day):
            block_start = start_dt + timedelta(minutes=b * (block_min + gap_min))
            block_end = block_start + timedelta(minutes=block_min)

            e = Event()
            e.name = title
            e.begin = block_start
            e.end = block_end
            c.events.add(e)

    # Save ICS file
    path, _ = QFileDialog.getSaveFileName(parent, "Save Study Blocks", "studyblocks.ics", "iCalendar Files (*.ics)")
    if not path:
        return
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(c.serialize())

    QMessageBox.information(parent, "Study Blocks", f"Saved {len(c.events)} study blocks to {os.path.basename(path)}.\nImport it into your calendar app.")