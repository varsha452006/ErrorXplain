"""
tests/test_ui.py
----------------
Headless automated test suite for ErrorXplain Desktop UI.

Executes tests on:
- Window construction & styling
- Sample loading & Analyze button
- Badge updates (Category, Language, Severity, Source)
- Clear button behavior
- History dialog & Restore functionality
- Report Unknown Error feedback dialog
"""

import unittest
import sys
import os

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ui.main_window import MainWindow
from ui.dialogs import ErrorHistoryDialog, ReportUnknownErrorDialog
from core.engine_interface import DiagnosticResult, RuleEngineInterface
from mock_engine import MockRuleEngine

# Single QApplication instance for tests
app = QApplication.instance()
if app is None:
    app = QApplication(["-platform", "offscreen"])


class TestErrorXplainUI(unittest.TestCase):

    def setUp(self):
        self.engine = MockRuleEngine()
        self.window = MainWindow(engine=self.engine)

    def tearDown(self):
        self.window.close()

    def test_01_initial_state(self):
        """Verify the window initializes in the empty placeholder state."""
        self.assertTrue(self.window.windowTitle().startswith("ErrorXplain"))
        self.assertEqual(self.window.result_stack.currentIndex(), 0)
        self.assertEqual(self.window.error_input.toPlainText(), "")

    def test_02_sample_loader(self):
        """Verify quick samples correctly fill the input text box."""
        samples = self.window.engine.get_sample_errors()
        self.assertIn("C++ Syntax Error", samples)
        cpp_sample = samples["C++ Syntax Error"]

        self.window.load_sample_error(cpp_sample)
        self.assertEqual(self.window.error_input.toPlainText(), cpp_sample)

    def test_03_analyze_cpp_error(self):
        """Verify analyzing C++ compiler diagnostics renders appropriate fields and badges."""
        samples = self.window.engine.get_sample_errors()
        self.window.load_sample_error(samples["C++ Syntax Error"])
        self.window.on_analyze_clicked()

        self.assertEqual(self.window.result_stack.currentIndex(), 1)
        self.assertIn("C++", self.window.language_badge.text())
        self.assertIn("Syntax Error", self.window.category_badge.text())
        self.assertIn("ERROR", self.window.severity_badge.text())
        self.assertGreater(len(self.window.explanation_text.text()), 15)
        self.assertGreater(len(self.window.suggested_action_text.text()), 15)

    def test_04_analyze_python_error(self):
        """Verify analyzing Python traceback correctly identifies zero division."""
        samples = self.window.engine.get_sample_errors()
        self.window.load_sample_error(samples["Python Runtime Error"])
        self.window.on_analyze_clicked()

        self.assertEqual(self.window.result_stack.currentIndex(), 1)
        self.assertIn("Python", self.window.language_badge.text())
        self.assertIn("Zero Division", self.window.category_badge.text())
        self.assertIn("ERROR", self.window.severity_badge.text())

    def test_05_clear_action(self):
        """Verify clear resets input and reverts Latest Error to empty placeholder."""
        samples = self.window.engine.get_sample_errors()
        self.window.load_sample_error(samples["C Linker Error"])
        self.window.on_analyze_clicked()
        self.assertEqual(self.window.result_stack.currentIndex(), 1)

        self.window.clear_all()
        self.assertEqual(self.window.error_input.toPlainText(), "")
        self.assertIsNone(self.window.current_result)
        self.assertEqual(self.window.result_stack.currentIndex(), 0)

    def test_06_history_dialog(self):
        """Verify error history populates and can restore an error into the main window."""
        dialog = ErrorHistoryDialog(self.window.engine, self.window)
        dialog.load_error_requested.connect(self.window.load_from_history)

        self.assertGreaterEqual(dialog.table.rowCount(), 2)

        # Select first row
        dialog.table.selectRow(0)
        dialog.on_row_selected()
        self.assertTrue(dialog.load_btn.isEnabled())
        self.assertGreater(len(dialog.preview_text.toPlainText()), 10)

        # Restore error
        dialog.load_selected_error()
        self.assertEqual(self.window.result_stack.currentIndex(), 1)
        self.assertNotEqual(self.window.error_input.toPlainText(), "")

    def test_07_report_unknown_error_dialog(self):
        """Verify report unknown error dialog initializes with prefilled error and engine."""
        self.window.error_input.setPlainText("unrecognized_symbol_error_sample")
        dialog = ReportUnknownErrorDialog(
            engine=self.window.engine,
            default_error_text=self.window.error_input.toPlainText(),
            parent=self.window
        )

        self.assertEqual(dialog.error_input.toPlainText(), "unrecognized_symbol_error_sample")
        self.assertGreaterEqual(dialog.lang_combo.count(), 3)
        self.assertIs(dialog.engine, self.window.engine)

    def test_08_dependency_injection_contract(self):
        """Verify MainWindow enforces the RuleEngineInterface contract."""
        self.assertIsInstance(self.window.engine, RuleEngineInterface)

        # Verify None engine raises ValueError
        with self.assertRaises(ValueError):
            MainWindow(engine=None)


if __name__ == "__main__":
    unittest.main()
