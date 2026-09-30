"""
core/engine_interface.py
------------------------
Neutral domain contracts and data models for ErrorXplain.

Defines the contract between:
- Desktop UI (Member 1)
- Rule Engine & Parser (Member 3)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class DiagnosticResult:
    """Represents the structured diagnostic output for an analyzed error."""
    category: str
    source: str
    language: str
    severity: str  # "Error", "Warning", "Fatal"
    original_error: str
    explanation: str
    suggested_action: str
    timestamp: str


class RuleEngineInterface(ABC):
    """
    Abstract interface defining the contract between ErrorXplain Desktop UI (Member 1)
    and diagnostic rule engines (Member 3).
    """

    @abstractmethod
    def analyze(
        self,
        raw_text: str,
        source: str = "Manual Input"
    ) -> DiagnosticResult:
        """Translates raw diagnostic text into a structured DiagnosticResult."""
        pass

    @abstractmethod
    def get_sample_errors(self) -> Dict[str, str]:
        """Provides realistic sample errors for instant testing/demonstrations."""
        pass

    @abstractmethod
    def get_history(self) -> List[DiagnosticResult]:
        """Returns the list of analyzed diagnostics."""
        pass

    @abstractmethod
    def clear_history(self) -> None:
        """Clears the diagnostic history."""
        pass

    @abstractmethod
    def report_unknown_error(
        self,
        raw_text: str,
        language: str,
        compiler_info: str,
        notes: str
    ) -> Dict[str, str]:
        """Records an unparsed or misdiagnosed error report for offline feedback."""
        pass

    @abstractmethod
    def get_ai_suggestion(
        self,
        raw_text: str,
        language: str
    ) -> Dict:
        """
        Requests an AI suggestion explicitly requested by the user.

        Normal analysis must remain offline-first. This method is
        called only when the user clicks the 'Give AI Suggestion'
        button.
        """
        pass