"""
ui/dialogs.py
-------------
Modal dialogs for Error History and Unknown Error Reporting in ErrorXplain.
"""

from typing import List, Optional, Callable
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QPlainTextEdit,
    QLineEdit, QComboBox, QMessageBox, QFrame, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.engine_interface import DiagnosticResult, RuleEngineInterface
import styles


class ErrorHistoryDialog(QDialog):
    """Dialog displaying session error diagnostic history."""

    # Signal emitted when the user selects a historical item to load into the main window
    load_error_requested = pyqtSignal(DiagnosticResult)

    def __init__(self, engine: RuleEngineInterface, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("Error History - ErrorXplain")
        self.resize(750, 500)
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.populate_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        title = QLabel("Error Diagnostic History")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0f172a;")
        subtitle = QLabel("Review past diagnostic explanations from this session.")
        subtitle.setStyleSheet("font-size: 11px; color: #475569;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # Splitter with Table and Preview
        splitter = QSplitter(Qt.Vertical)

        # Table of history items
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Language", "Category", "Severity", "Error Preview"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        splitter.addWidget(self.table)

        # Preview Area for selected item
        preview_frame = QFrame()
        preview_frame.setObjectName("innerCardFrame")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(10, 8, 10, 8)
        preview_layout.setSpacing(4)

        preview_label = QLabel("Selected Explanation Preview:")
        preview_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        preview_layout.addWidget(preview_label)

        self.preview_text = QPlainTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 3px; font-size: 12px; padding: 6px; color: #0f172a;"
        )
        self.preview_text.setPlaceholderText("Select a row above to preview its plain-language explanation...")
        preview_layout.addWidget(self.preview_text)

        splitter.addWidget(preview_frame)
        splitter.setSizes([260, 160])
        layout.addWidget(splitter)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.setObjectName("dangerBtn")
        self.clear_btn.clicked.connect(self.clear_history)
        btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch()

        self.load_btn = QPushButton("Load into Main Window")
        self.load_btn.setObjectName("primaryBtn")
        self.load_btn.setEnabled(False)
        self.load_btn.clicked.connect(self.load_selected_error)
        btn_layout.addWidget(self.load_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("secondaryBtn")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def populate_table(self):
        """Populates the history table from the mock engine."""
        history = self.engine.get_history()
        self.table.setRowCount(len(history))
        for row, item in enumerate(history):
            self.table.setItem(row, 0, QTableWidgetItem(item.timestamp))
            self.table.setItem(row, 1, QTableWidgetItem(item.language))
            self.table.setItem(row, 2, QTableWidgetItem(item.category))
            self.table.setItem(row, 3, QTableWidgetItem(item.severity))

            # Short preview of first line
            preview = item.original_error.split("\n")[0]
            if len(preview) > 65:
                preview = preview[:62] + "..."
            self.table.setItem(row, 4, QTableWidgetItem(preview))

    def on_row_selected(self):
        """Updates the preview area when a row is clicked."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            history = self.engine.get_history()
            if 0 <= row < len(history):
                item = history[row]
                self.preview_text.setPlainText(
                    f"Category: {item.category} ({item.language})\n"
                    f"Severity: {item.severity}\n\n"
                    f"Explanation:\n{item.explanation}\n\n"
                    f"Suggested Fix:\n{item.suggested_action}"
                )
                self.load_btn.setEnabled(True)
                return
        self.preview_text.clear()
        self.load_btn.setEnabled(False)

    def load_selected_error(self):
        """Emits signal to load selected item in the main window and closes dialog."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            history = self.engine.get_history()
            if 0 <= row < len(history):
                self.load_error_requested.emit(history[row])
                self.accept()

    def clear_history(self):
        """Clears all session history."""
        confirm = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear all recorded error history for this session?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.engine.clear_history()
            self.populate_table()
            self.preview_text.clear()
            self.load_btn.setEnabled(False)


class ReportUnknownErrorDialog(QDialog):
    """Dialog for user feedback on unknown or misparsed compiler diagnostics."""

    def __init__(self, engine: Optional[RuleEngineInterface] = None, default_error_text: str = "", parent=None):
        super().__init__(parent)
        self.engine = engine
        self.default_error_text = default_error_text
        self.setWindowTitle("Report Unknown Error - ErrorXplain")
        self.resize(550, 480)
        self.setMinimumSize(450, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        title = QLabel("Report Unknown or Unclear Diagnostic")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0f172a;")
        desc = QLabel(
            "Help expand ErrorXplain's rule engine! Unrecognized errors are saved "
            "locally so our rule engine contributors can add translation patterns."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 11px; color: #475569; line-height: 1.4;")
        header_layout.addWidget(title)
        header_layout.addWidget(desc)
        layout.addLayout(header_layout)

        # Form Container
        form_frame = QFrame()
        form_frame.setObjectName("cardFrame")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(12, 10, 12, 10)
        form_layout.setSpacing(8)

        # Error Text Input
        err_label = QLabel("Diagnostic Message:")
        err_label.setStyleSheet("font-weight: 600; font-size: 11px; color: #374151;")
        form_layout.addWidget(err_label)

        self.error_input = QPlainTextEdit()
        self.error_input.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 3px; font-family: 'Consolas', 'Cascadia Code', monospace; font-size: 11px; padding: 6px;"
        )
        self.error_input.setPlainText(self.default_error_text)
        self.error_input.setPlaceholderText("Paste the unparsed error message here...")
        form_layout.addWidget(self.error_input)

        # Language Selection Row
        lang_row = QHBoxLayout()
        lang_label = QLabel("Language / Compiler:")
        lang_label.setStyleSheet("font-weight: 600; font-size: 11px; color: #374151;")
        lang_row.addWidget(lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["C++ (g++ / clang++)", "Python 3", "C (gcc / clang)", "MSVC", "Other"])
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch()
        form_layout.addLayout(lang_row)

        # Optional Notes
        notes_label = QLabel("Additional Notes / Code context (optional):")
        notes_label.setStyleSheet("font-weight: 600; font-size: 11px; color: #374151;")
        form_layout.addWidget(notes_label)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("e.g. Occurred when compiling with -std=c++20...")
        form_layout.addWidget(self.notes_input)

        layout.addWidget(form_frame)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.submit_btn = QPushButton("Save Offline Report")
        self.submit_btn.setObjectName("primaryBtn")
        self.submit_btn.clicked.connect(self.submit_report)
        btn_layout.addWidget(self.submit_btn)

        layout.addLayout(btn_layout)

    def submit_report(self):
        """Validates and processes the feedback submission."""
        error_text = self.error_input.toPlainText().strip()
        if not error_text:
            QMessageBox.warning(self, "Missing Content", "Please enter the diagnostic message before submitting.")
            return

        lang = self.lang_combo.currentText()
        notes = self.notes_input.text()

        # Record into engine feedback queue if available
        if self.engine:
            self.engine.report_unknown_error(
                raw_text=error_text,
                language=lang,
                compiler_info="",
                notes=notes
            )

        # Show success confirmation modal
        QMessageBox.information(
            self,
            "Feedback Queued (Offline)",
            "Diagnostic report has been recorded in the local feedback queue.\n\n"
            "Status: Saved locally.\n"
            "This will help Member 3 train and expand the offline rule engine.",
            QMessageBox.Ok
        )
        self.accept()
