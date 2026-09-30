"""
Main application window for ErrorXplain Desktop UI.

Implements:
1. Application Header
2. Error Input Section
3. Latest Error Section
4. Optional AI Suggestion
5. Bottom Action Bar
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QFrame,
    QScrollArea,
    QStackedWidget,
    QApplication,
    QMessageBox,
    QStatusBar,
)

from PyQt5.QtCore import Qt

from core.engine_interface import RuleEngineInterface, DiagnosticResult
from ui.dialogs import ErrorHistoryDialog, ReportUnknownErrorDialog
import styles


class MainWindow(QMainWindow):
    """Primary application window for ErrorXplain Desktop."""

    def __init__(self, engine: RuleEngineInterface):
        super().__init__()

        if engine is None:
            raise ValueError(
                "An engine instance implementing RuleEngineInterface "
                "must be provided to MainWindow."
            )

        self.engine: RuleEngineInterface = engine
        self.current_result: DiagnosticResult = None

        self.setWindowTitle(
            "ErrorXplain - Compiler & Runtime Diagnostic Translator"
        )
        self.resize(1000, 760)
        self.setMinimumSize(850, 620)

        # Apply global application stylesheet
        self.setStyleSheet(styles.MAIN_STYLESHEET)

        self.setup_ui()
        self.setup_status_bar()

    def setup_ui(self):
        """Constructs the primary UI layout."""

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Root vertical layout
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(18, 14, 18, 12)
        root_layout.setSpacing(10)

        # 1. Header Section
        header_widget = self.create_header()
        root_layout.addWidget(header_widget)

        # Main Scrollable Body
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 2, 0)
        content_layout.setSpacing(10)

        # 2. Error Input Section
        input_card = self.create_input_section()
        content_layout.addWidget(input_card)

        # 3. Latest Error Section
        self.latest_error_card = self.create_latest_error_section()
        content_layout.addWidget(self.latest_error_card)

        scroll_area.setWidget(content_container)
        root_layout.addWidget(scroll_area, stretch=1)

        # 4. Bottom Action Bar
        action_bar = self.create_action_bar()
        root_layout.addWidget(action_bar)

    def create_header(self) -> QWidget:
        """Builds the top branding and header section."""

        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(14, 8, 14, 8)

        # Left: App Branding
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel("ErrorXplain")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #0f172a;"
        )

        subtitle_label = QLabel(
            "Understand programming errors. Fix them faster."
        )
        subtitle_label.setStyleSheet(
            "font-size: 11px; color: #475569; font-weight: 400;"
        )

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        # Right: Backend Status Indicator
        status_pill = QLabel("• Connected to ErrorXplain Engine")
        status_pill.setStyleSheet(
            """
            background-color: #f8fafc;
            color: #047857;
            border: 1px solid #cbd5e1;
            border-radius: 3px;
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            """
        )

        header_layout.addWidget(
            status_pill,
            alignment=Qt.AlignVCenter
        )

        return header_frame

    def create_input_section(self) -> QFrame:
        """Builds the diagnostic input panel with sample error loaders."""

        card = QFrame()
        card.setObjectName("cardFrame")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Section Title and Sample Loaders Row
        top_row = QHBoxLayout()

        section_title = QLabel("ERROR INPUT")
        section_title.setStyleSheet(
            "font-size: 11px; font-weight: 700; "
            "color: #374151; letter-spacing: 0.5px;"
        )

        top_row.addWidget(section_title)
        top_row.addStretch()

        sample_hint = QLabel("Quick Samples:")
        sample_hint.setStyleSheet(
            "font-size: 11px; color: #64748b; font-weight: 500;"
        )

        top_row.addWidget(sample_hint)

        # Sample Load Buttons
        samples = self.engine.get_sample_errors()

        for sample_name, sample_text in samples.items():
            btn = QPushButton(sample_name)
            btn.setObjectName("sampleChip")

            btn.clicked.connect(
                lambda checked=False, txt=sample_text:
                self.load_sample_error(txt)
            )

            top_row.addWidget(btn)

        layout.addLayout(top_row)

        # Multiline Input Box
        self.error_input = QPlainTextEdit()
        self.error_input.setObjectName("errorInput")

        self.error_input.setPlaceholderText(
            "Paste compiler diagnostics or runtime traceback here...\n"
            "(e.g., g++/clang errors, linker messages, Python Traceback)"
        )

        self.error_input.setMinimumHeight(115)
        self.error_input.setMaximumHeight(160)

        layout.addWidget(self.error_input)

        # Bottom Button Row for Input Panel
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        input_hint = QLabel(
            "Supports C, C++, Python and Java diagnostics"
        )
        input_hint.setStyleSheet(
            "font-size: 11px; color: #64748b;"
        )

        btn_row.addWidget(input_hint)
        btn_row.addStretch()

        self.clear_input_btn = QPushButton("Clear Input")
        self.clear_input_btn.setObjectName("secondaryBtn")
        self.clear_input_btn.clicked.connect(
            self.clear_input_only
        )

        btn_row.addWidget(self.clear_input_btn)

        self.analyze_btn = QPushButton("Analyze Error")
        self.analyze_btn.setObjectName("primaryBtn")
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_btn.clicked.connect(
            self.on_analyze_clicked
        )

        btn_row.addWidget(self.analyze_btn)

        layout.addLayout(btn_row)

        return card

    def create_latest_error_section(self) -> QFrame:
        """Builds the results section containing empty and populated states."""

        card = QFrame()
        card.setObjectName("cardFrame")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Section Header
        section_title = QLabel("LATEST ERROR EXPLANATION")
        section_title.setStyleSheet(
            "font-size: 11px; font-weight: 700; "
            "color: #374151; letter-spacing: 0.5px;"
        )

        layout.addWidget(section_title)

        # Stacked Widget
        self.result_stack = QStackedWidget()

        # State 0: Empty / Placeholder View
        self.empty_widget = self.create_empty_state_view()
        self.result_stack.addWidget(self.empty_widget)

        # State 1: Populated Diagnostic View
        self.result_widget = self.create_diagnostic_result_view()
        self.result_stack.addWidget(self.result_widget)

        layout.addWidget(self.result_stack)

        return card

    def create_empty_state_view(self) -> QWidget:
        """Placeholder widget shown before an error is analyzed."""

        container = QFrame()
        container.setObjectName("innerCardFrame")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        title_label = QLabel("No diagnostic analyzed yet")
        title_label.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #374151;"
        )
        title_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)

        hint_label = QLabel(
            "Paste a diagnostic message into the editor above "
            "or select a 'Quick Sample', then click 'Analyze Error'."
        )
        hint_label.setStyleSheet(
            "font-size: 11px; color: #64748b;"
        )
        hint_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(hint_label)

        return container

    def create_diagnostic_result_view(self) -> QWidget:
        """Widget displaying all diagnostic outputs."""

        container = QWidget()

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # ---------------------------------------------------------
        # 1. Metadata Row
        # ---------------------------------------------------------

        meta_bar = QFrame()
        meta_bar.setObjectName("metadataBar")

        meta_layout = QHBoxLayout(meta_bar)
        meta_layout.setContentsMargins(10, 6, 10, 6)
        meta_layout.setSpacing(8)

        # Language Badge
        self.language_badge = QLabel("Language: C++")
        self.language_badge.setStyleSheet(
            styles.get_meta_badge_style("language")
        )
        meta_layout.addWidget(self.language_badge)

        # Category Badge
        self.category_badge = QLabel(
            "Category: Syntax Error"
        )
        self.category_badge.setStyleSheet(
            styles.get_meta_badge_style("category")
        )
        meta_layout.addWidget(self.category_badge)

        # Severity Badge
        self.severity_badge = QLabel(
            "Severity: Error"
        )
        self.severity_badge.setStyleSheet(
            styles.get_severity_badge_style("Error")
        )
        meta_layout.addWidget(self.severity_badge)

        # Source Badge
        self.source_badge = QLabel(
            "Source: Manual Input"
        )
        self.source_badge.setStyleSheet(
            styles.get_meta_badge_style("source")
        )
        meta_layout.addWidget(self.source_badge)

        meta_layout.addStretch()

        # Timestamp
        self.timestamp_label = QLabel("")
        self.timestamp_label.setStyleSheet(
            "font-size: 11px; color: #64748b;"
        )
        meta_layout.addWidget(self.timestamp_label)

        layout.addWidget(meta_bar)

        # ---------------------------------------------------------
        # 2. Original Error Message
        # ---------------------------------------------------------

        original_frame = QFrame()
        original_frame.setObjectName("consoleFrame")

        orig_layout = QVBoxLayout(original_frame)
        orig_layout.setContentsMargins(12, 8, 12, 10)
        orig_layout.setSpacing(6)

        orig_header_layout = QHBoxLayout()

        orig_title = QLabel(
            "ORIGINAL DIAGNOSTIC MESSAGE"
        )
        orig_title.setStyleSheet(
            "font-size: 10px; font-weight: 700; "
            "color: #94a3b8; letter-spacing: 0.5px;"
        )

        orig_header_layout.addWidget(orig_title)
        orig_header_layout.addStretch()

        copy_btn = QPushButton("Copy")

        copy_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #27272a;
                color: #d4d4d8;
                border: 1px solid #3f3f46;
                border-radius: 3px;
                font-size: 11px;
                padding: 2px 8px;
            }

            QPushButton:hover {
                background-color: #3f3f46;
                color: #ffffff;
            }

            QPushButton:pressed {
                background-color: #18181b;
            }
            """
        )

        copy_btn.clicked.connect(
            self.copy_original_error
        )

        orig_header_layout.addWidget(copy_btn)
        orig_layout.addLayout(orig_header_layout)

        self.original_error_text = QLabel()

        self.original_error_text.setStyleSheet(
            "color: #f4f4f5; "
            "font-family: 'Consolas', 'Cascadia Code', "
            "'Courier New', monospace; "
            "font-size: 12px; line-height: 1.45;"
        )

        self.original_error_text.setWordWrap(True)
        self.original_error_text.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        orig_layout.addWidget(
            self.original_error_text
        )

        layout.addWidget(original_frame)

        # ---------------------------------------------------------
        # 3. Plain-Language Explanation
        # ---------------------------------------------------------

        exp_frame = QFrame()
        exp_frame.setObjectName("explanationFrame")

        exp_layout = QVBoxLayout(exp_frame)
        exp_layout.setContentsMargins(14, 10, 14, 10)
        exp_layout.setSpacing(4)

        exp_title = QLabel(
            "PLAIN-LANGUAGE EXPLANATION"
        )
        exp_title.setStyleSheet(
            "font-size: 11px; font-weight: 700; "
            "color: #1e293b; letter-spacing: 0.5px;"
        )

        exp_layout.addWidget(exp_title)

        self.explanation_text = QLabel()
        self.explanation_text.setStyleSheet(
            "font-size: 13px; color: #0f172a; line-height: 1.5;"
        )
        self.explanation_text.setWordWrap(True)
        self.explanation_text.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        exp_layout.addWidget(
            self.explanation_text
        )

        layout.addWidget(exp_frame)

        # ---------------------------------------------------------
        # 4. Suggested Corrective Action
        # ---------------------------------------------------------

        action_frame = QFrame()
        action_frame.setObjectName("actionFrame")

        action_layout = QVBoxLayout(action_frame)
        action_layout.setContentsMargins(14, 10, 14, 10)
        action_layout.setSpacing(4)

        action_title = QLabel(
            "SUGGESTED CORRECTIVE ACTION"
        )
        action_title.setStyleSheet(
            "font-size: 11px; font-weight: 700; "
            "color: #1e293b; letter-spacing: 0.5px;"
        )

        action_layout.addWidget(action_title)

        self.suggested_action_text = QLabel()
        self.suggested_action_text.setStyleSheet(
            "font-size: 13px; color: #0f172a; line-height: 1.5;"
        )
        self.suggested_action_text.setWordWrap(True)
        self.suggested_action_text.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        action_layout.addWidget(
            self.suggested_action_text
        )

        layout.addWidget(action_frame)

        # ---------------------------------------------------------
        # 5. Give AI Suggestion Button
        # ---------------------------------------------------------

        self.ai_suggestion_btn = QPushButton(
            "Give AI Suggestion"
        )

        self.ai_suggestion_btn.setObjectName(
            "primaryBtn"
        )

        self.ai_suggestion_btn.setCursor(
            Qt.PointingHandCursor
        )

        self.ai_suggestion_btn.clicked.connect(
            self.on_ai_suggestion_clicked
        )

        # Hidden initially.
        # It will only appear when the offline engine
        # cannot identify the error.
        self.ai_suggestion_btn.setVisible(False)

        layout.addWidget(
            self.ai_suggestion_btn,
            alignment=Qt.AlignLeft
        )

        return container

    def create_action_bar(self) -> QWidget:
        """Builds the bottom controls."""

        action_bar = QFrame()

        layout = QHBoxLayout(action_bar)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(8)

        # Error History Button
        self.history_btn = QPushButton(
            "Error History"
        )
        self.history_btn.setObjectName(
            "secondaryBtn"
        )
        self.history_btn.setCursor(
            Qt.PointingHandCursor
        )
        self.history_btn.clicked.connect(
            self.open_history_dialog
        )

        layout.addWidget(
            self.history_btn
        )

        layout.addStretch()

        # Clear Button
        self.clear_all_btn = QPushButton(
            "Clear"
        )
        self.clear_all_btn.setObjectName(
            "dangerBtn"
        )
        self.clear_all_btn.setCursor(
            Qt.PointingHandCursor
        )
        self.clear_all_btn.clicked.connect(
            self.clear_all
        )

        layout.addWidget(
            self.clear_all_btn
        )

        # Report Unknown Error Button
        self.report_btn = QPushButton(
            "Report Unknown Error"
        )
        self.report_btn.setObjectName(
            "secondaryBtn"
        )
        self.report_btn.setCursor(
            Qt.PointingHandCursor
        )
        self.report_btn.clicked.connect(
            self.open_report_dialog
        )

        layout.addWidget(
            self.report_btn
        )

        return action_bar

    def setup_status_bar(self):
        """Initializes the bottom status bar."""

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_bar.showMessage(
            "Ready. Paste an error message to translate."
        )

    # -------------------------------------------------------------------------
    # Core Actions and Event Handlers
    # -------------------------------------------------------------------------

    def on_analyze_clicked(self):
        """
        Processes the error text using the offline-first engine.

        AI is NOT requested during normal analysis.
        """

        text = self.error_input.toPlainText().strip()

        if not text:
            QMessageBox.information(
                self,
                "No Input Provided",
                "Please paste a diagnostic message into the "
                "text box, or click one of the 'Quick Samples' above.",
                QMessageBox.Ok,
            )
            return

        # Normal analysis.
        # ApiRuleEngine sends allow_ai=False.
        result = self.engine.analyze(
            text,
            source="Manual Input"
        )

        self.display_result(result)

        self.status_bar.showMessage(
            f"Analyzed {result.language} diagnostic: "
            f"{result.category} [{result.severity}]"
        )

    def display_result(self, result: DiagnosticResult):
        """Renders a DiagnosticResult object into the Latest Error section."""

        self.current_result = result

        # ---------------------------------------------------------
        # 1. Update badges
        # ---------------------------------------------------------

        self.category_badge.setText(
            f"Category: {result.category}"
        )

        self.language_badge.setText(
            f"Language: {result.language}"
        )

        self.severity_badge.setText(
            f"Severity: {result.severity.upper()}"
        )

        self.severity_badge.setStyleSheet(
            styles.get_severity_badge_style(
                result.severity
            )
        )

        self.source_badge.setText(
            f"Source: {result.source}"
        )

        self.timestamp_label.setText(
            f"Analyzed at: {result.timestamp}"
        )

        # ---------------------------------------------------------
        # 2. Update text sections
        # ---------------------------------------------------------

        self.original_error_text.setText(
            result.original_error
        )

        self.explanation_text.setText(
            result.explanation
        )

        self.suggested_action_text.setText(
            result.suggested_action
        )

        # ---------------------------------------------------------
        # 3. Show AI button only for unknown errors
        # ---------------------------------------------------------

        is_unknown_error = (
            result.category.strip().lower()
            == "unknown"
        )

        self.ai_suggestion_btn.setVisible(
            is_unknown_error
        )

        self.ai_suggestion_btn.setEnabled(
            True
        )

        self.ai_suggestion_btn.setText(
            "Give AI Suggestion"
        )

        # ---------------------------------------------------------
        # 4. Switch to result view
        # ---------------------------------------------------------

        self.result_stack.setCurrentIndex(1)

    def on_ai_suggestion_clicked(self):
        """
        Requests an AI suggestion only after explicit user action.

        The normal Analyze Error operation never calls AI.
        """

        if not self.current_result:
            return

        raw_text = (
            self.current_result.original_error.strip()
        )

        if not raw_text:
            return

        # Use the language detected during the original analysis.
        language = (
            self.current_result.language.lower()
        )

        # ---------------------------------------------------------
        # Disable button while AI request is running
        # ---------------------------------------------------------

        self.ai_suggestion_btn.setEnabled(False)

        self.ai_suggestion_btn.setText(
            "Getting AI Suggestion..."
        )

        self.status_bar.showMessage(
            "Requesting AI suggestion..."
        )

        # Allow the UI to update before the network request.
        QApplication.processEvents()

        try:
            # This method sends allow_ai=True.
            api_result = self.engine.get_ai_suggestion(
                raw_text,
                language
            )

            # -----------------------------------------------------
            # Convert backend severity to UI severity
            # -----------------------------------------------------

            severity_mapping = {
                "Low": "Warning",
                "Medium": "Error",
                "High": "Error",
                "Critical": "Fatal",
            }

            backend_severity = api_result.get(
                "severity",
                "Medium"
            )

            severity = severity_mapping.get(
                backend_severity,
                "Error"
            )

            # -----------------------------------------------------
            # Build AI DiagnosticResult
            # -----------------------------------------------------

            ai_result = DiagnosticResult(
                category=api_result.get(
                    "category",
                    "Unknown"
                ),
                source="AI Suggestion",
                language=api_result.get(
                    "language",
                    language
                ),
                severity=severity,
                original_error=raw_text,
                explanation=api_result.get(
                    "explanation",
                    "The AI did not return an explanation."
                ),
                suggested_action=api_result.get(
                    "suggestion",
                    "The AI did not return a corrective action."
                ),
                timestamp=datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )

            # -----------------------------------------------------
            # Store AI result
            # -----------------------------------------------------

            self.current_result = ai_result

            # -----------------------------------------------------
            # Update UI
            # -----------------------------------------------------

            self.category_badge.setText(
                f"Category: {ai_result.category}"
            )

            self.language_badge.setText(
                f"Language: {ai_result.language}"
            )

            self.severity_badge.setText(
                f"Severity: {ai_result.severity.upper()}"
            )

            self.severity_badge.setStyleSheet(
                styles.get_severity_badge_style(
                    ai_result.severity
                )
            )

            self.source_badge.setText(
                "Source: AI Suggestion"
            )

            self.timestamp_label.setText(
                f"Analyzed at: {ai_result.timestamp}"
            )

            self.original_error_text.setText(
                ai_result.original_error
            )

            self.explanation_text.setText(
                ai_result.explanation
            )

            self.suggested_action_text.setText(
                ai_result.suggested_action
            )

            # -----------------------------------------------------
            # AI succeeded
            # -----------------------------------------------------

            self.ai_suggestion_btn.setEnabled(
                True
            )

            self.ai_suggestion_btn.setText(
                "Give AI Suggestion"
            )

            self.status_bar.showMessage(
                "AI suggestion received."
            )

        except Exception:
            # -----------------------------------------------------
            # AI failed.
            #
            # Do NOT crash the application.
            # Offline functionality remains available.
            # -----------------------------------------------------

            self.explanation_text.setText(
                "AI suggestion is currently unavailable. "
                "No internet connection or AI service "
                "could be reached."
            )

            self.suggested_action_text.setText(
                "You can continue using ErrorXplain's "
                "offline diagnostic rules, or try the "
                "AI suggestion again later."
            )

            self.source_badge.setText(
                "Source: Default"
            )

            self.ai_suggestion_btn.setEnabled(
                True
            )

            self.ai_suggestion_btn.setText(
                "Give AI Suggestion"
            )

            self.status_bar.showMessage(
                "AI suggestion unavailable. "
                "Offline mode remains available."
            )

    def load_sample_error(self, sample_text: str):
        """Fills the input box with a selected sample diagnostic."""

        self.error_input.setPlainText(
            sample_text
        )

        self.status_bar.showMessage(
            "Loaded sample diagnostic into input box."
        )

    def copy_original_error(self):
        """Copies the original diagnostic message to the clipboard."""

        if self.current_result:
            clipboard = QApplication.clipboard()

            clipboard.setText(
                self.current_result.original_error
            )

            self.status_bar.showMessage(
                "Original error copied to clipboard.",
                3000
            )

    def clear_input_only(self):
        """Clears only the input text area."""

        self.error_input.clear()

        self.status_bar.showMessage(
            "Input cleared."
        )

    def clear_all(self):
        """
        Clears both the input box and resets
        the Latest Error section to empty state.
        """

        self.error_input.clear()
        self.current_result = None

        # Hide AI button when results are cleared.
        self.ai_suggestion_btn.setVisible(False)
        self.ai_suggestion_btn.setEnabled(True)
        self.ai_suggestion_btn.setText(
            "Give AI Suggestion"
        )

        self.result_stack.setCurrentIndex(0)

        self.status_bar.showMessage(
            "Input and results cleared."
        )

    def open_history_dialog(self):
        """Opens the modal dialog displaying error history."""

        dialog = ErrorHistoryDialog(
            self.engine,
            self
        )

        dialog.load_error_requested.connect(
            self.load_from_history
        )

        dialog.exec_()

    def load_from_history(self, item: DiagnosticResult):
        """Loads an error selected from history into the main display."""

        self.error_input.setPlainText(
            item.original_error
        )

        self.display_result(item)

        self.status_bar.showMessage(
            f"Restored error from history ({item.timestamp})."
        )

    def open_report_dialog(self):
        """Opens the modal dialog for reporting an unknown error."""

        default_text = (
            self.error_input.toPlainText().strip()
        )

        dialog = ReportUnknownErrorDialog(
            engine=self.engine,
            default_error_text=default_text,
            parent=self
        )

        dialog.exec_()