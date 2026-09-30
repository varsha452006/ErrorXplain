"""
styles.py
---------
Centralized design system and Qt Stylesheet (QSS) for ErrorXplain Desktop UI.
Implements a restrained, professional desktop engineering and developer tool
visual language (subtle borders, clean typography, compact metadata, monospace
console panels, and semantic color usage).
"""

# Global Application Stylesheet
MAIN_STYLESHEET = """
/* Global Window & Dialog Styling */
QMainWindow {
    background-color: #f1f3f5;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
}

QDialog {
    background-color: #f1f3f5;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    color: #111827;
}

/* Scroll Area & Scrollbars */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #e5e7eb;
    width: 8px;
    margin: 0px;
    border-radius: 2px;
}

QScrollBar::handle:vertical {
    background: #9ca3af;
    min-height: 24px;
    border-radius: 2px;
}

QScrollBar::handle:vertical:hover {
    background: #6b7280;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Top App Header Frame */
QFrame#headerFrame {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 3px;
    padding: 2px 0px;
}

/* Desktop Action Buttons */
QPushButton#primaryBtn {
    background-color: #1d4ed8;
    color: #ffffff;
    font-weight: 600;
    font-size: 12px;
    border: 1px solid #1e40af;
    border-radius: 3px;
    padding: 6px 16px;
    outline: none;
}

QPushButton#primaryBtn:hover {
    background-color: #1e40af;
    border-color: #172554;
}

QPushButton#primaryBtn:pressed {
    background-color: #172554;
}

QPushButton#primaryBtn:disabled {
    background-color: #94a3b8;
    border-color: #94a3b8;
    color: #f8fafc;
}

QPushButton#secondaryBtn {
    background-color: #ffffff;
    color: #1f2937;
    font-weight: 500;
    font-size: 12px;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    padding: 6px 14px;
    outline: none;
}

QPushButton#secondaryBtn:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
    color: #0f172a;
}

QPushButton#secondaryBtn:pressed {
    background-color: #f1f5f9;
}

QPushButton#secondaryBtn:disabled {
    background-color: #f8fafc;
    border-color: #e2e8f0;
    color: #94a3b8;
}

QPushButton#dangerBtn {
    background-color: #ffffff;
    color: #b91c1c;
    font-weight: 500;
    font-size: 12px;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    padding: 6px 14px;
    outline: none;
}

QPushButton#dangerBtn:hover {
    background-color: #fef2f2;
    border-color: #fca5a5;
    color: #991b1b;
}

QPushButton#dangerBtn:pressed {
    background-color: #fee2e2;
}

/* Quick Sample Tool Buttons */
QPushButton#sampleChip {
    background-color: #ffffff;
    color: #374151;
    font-size: 11px;
    font-weight: 500;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    padding: 3px 9px;
    outline: none;
}

QPushButton#sampleChip:hover {
    background-color: #f3f4f6;
    border-color: #9ca3af;
    color: #111827;
}

QPushButton#sampleChip:pressed {
    background-color: #e5e7eb;
}

/* Text Editors & Inputs */
QPlainTextEdit#errorInput {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    padding: 8px 10px;
    font-family: 'Consolas', 'Cascadia Code', 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.45;
}

QPlainTextEdit#errorInput:focus {
    border: 1px solid #2563eb;
    background-color: #ffffff;
}

QLineEdit, QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    padding: 5px 8px;
    font-size: 12px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #2563eb;
}

/* Desktop Panels / Group Frames */
QFrame#cardFrame {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 3px;
}

QFrame#innerCardFrame {
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 3px;
}

/* Diagnostic Result Panels */
QFrame#metadataBar {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 3px;
}

QFrame#consoleFrame {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 3px;
}

QFrame#explanationFrame {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #2563eb;
    border-radius: 3px;
}

QFrame#actionFrame {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #16a34a;
    border-radius: 3px;
}

/* Table View in Dialogs */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 2px;
    gridline-color: #e5e7eb;
    font-size: 12px;
}

QTableWidget::item {
    padding: 5px 8px;
}

QTableWidget::item:selected {
    background-color: #e0e7ff;
    color: #1e3a8a;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: 600;
    font-size: 11px;
    padding: 5px 8px;
    border: none;
    border-bottom: 1px solid #cbd5e1;
    border-right: 1px solid #e2e8f0;
}

/* Status Bar */
QStatusBar {
    background-color: #f8fafc;
    border-top: 1px solid #d1d5db;
    color: #4b5563;
    font-size: 11px;
}
"""

# Severity and Metadata Badge Styles
def get_severity_badge_style(severity: str) -> str:
    """Returns clean, restrained CSS for semantic severity indicators."""
    sev = severity.strip().capitalize()
    if sev in ["Fatal", "Critical"]:
        return """
            QLabel {
                background-color: #fef2f2;
                color: #991b1b;
                border: 1px solid #f87171;
                border-radius: 3px;
                padding: 2px 8px;
                font-weight: 700;
                font-size: 11px;
            }
        """
    elif sev in ["Error"]:
        return """
            QLabel {
                background-color: #fef2f2;
                color: #b91c1c;
                border: 1px solid #fca5a5;
                border-radius: 3px;
                padding: 2px 8px;
                font-weight: 700;
                font-size: 11px;
            }
        """
    elif sev in ["Warning"]:
        return """
            QLabel {
                background-color: #fffbeb;
                color: #b45309;
                border: 1px solid #fcd34d;
                border-radius: 3px;
                padding: 2px 8px;
                font-weight: 700;
                font-size: 11px;
            }
        """
    else:
        return """
            QLabel {
                background-color: #eff6ff;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
                border-radius: 3px;
                padding: 2px 8px;
                font-weight: 600;
                font-size: 11px;
            }
        """


def get_meta_badge_style(badge_type: str = "neutral") -> str:
    """Returns CSS for compact, technical metadata tags."""
    if badge_type == "language":
        return """
            QLabel {
                background-color: #f8fafc;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 3px;
                padding: 2px 8px;
                font-weight: 600;
                font-size: 11px;
            }
        """
    elif badge_type == "category":
        return """
            QLabel {
                background-color: #f8fafc;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 3px;
                padding: 2px 8px;
                font-weight: 600;
                font-size: 11px;
            }
        """
    elif badge_type == "source":
        return """
            QLabel {
                background-color: #f8fafc;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 3px;
                padding: 2px 8px;
                font-weight: 500;
                font-size: 11px;
            }
        """
    else:
        return """
            QLabel {
                background-color: #f8fafc;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 3px;
                padding: 2px 8px;
                font-weight: 500;
                font-size: 11px;
            }
        """

