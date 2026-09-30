"""
API-backed Rule Engine for ErrorXplain Desktop.

Connects the existing PyQt5 UI to the ErrorXplain-Team FastAPI backend.
"""

import json
import re
from datetime import datetime
from typing import List, Dict
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from core.engine_interface import DiagnosticResult, RuleEngineInterface


class ApiRuleEngine(RuleEngineInterface):
    """Rule engine implementation that communicates with the FastAPI backend."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.history: List[DiagnosticResult] = []
        self.feedback_queue: List[Dict[str, str]] = []

    def _detect_language(self, raw_text: str) -> str:
        """
        Detect the language from the diagnostic text.

        The current backend supports C, Python and Java.
        C++ is currently not supported by the backend's /explain
        language resolver.
        """
        text = raw_text.lower()

        # Python
        if (
            "traceback (most recent call last)" in text
            or "zerodivisionerror" in text
            or "nameerror" in text
            or "typeerror" in text
            or "indexerror" in text
            or "indentationerror" in text
            or re.search(r"\.py:\d+", text)
        ):
            return "python"

        # Java
        if (
            re.search(r"\.java:\d+", text)
            or "exception in thread" in text
            or "java.lang." in text
            or "cannot find symbol" in text
        ):
            return "java"

        # C++ indicators
        if (
            ".cpp:" in text
            or ".cc:" in text
            or ".cxx:" in text
            or "std::" in text
            or "cout" in text
            or "g++" in text
            or "clang++" in text
        ):
            return "cpp"

        # Default to C
        return "c"

    def _map_severity(self, severity: str) -> str:
        """
        Convert backend severity vocabulary to the existing UI vocabulary.
        """
        mapping = {
            "Low": "Warning",
            "Medium": "Error",
            "High": "Error",
            "Critical": "Fatal",
        }

        return mapping.get(severity, "Error")

    def _post_explain(self, raw_text: str, language: str) -> Dict:
        """Send an /explain request to the FastAPI backend."""

        payload = {
            "error_message": raw_text,
            "language": language,
            "source_code": None,
            "allow_ai": False,
        }

        request = Request(
            f"{self.base_url}/explain",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request, timeout=10) as response:
            response_data = response.read().decode("utf-8")
            return json.loads(response_data)

    def get_ai_suggestion(self, raw_text: str, language: str) -> Dict:
        """
        Request an AI suggestion explicitly requested by the user.

        AI is only enabled for this request. Normal error analysis
        remains offline-first and uses allow_ai=False.
        """

        payload = {
            "error_message": raw_text,
            "language": language,
            "source_code": None,
            "allow_ai": True,
        }

        request = Request(
            f"{self.base_url}/explain",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request, timeout=10) as response:
            response_data = response.read().decode("utf-8")
            return json.loads(response_data)

    def analyze(
        self,
        raw_text: str,
        source: str = "Manual Input"
    ) -> DiagnosticResult:

        cleaned = raw_text.strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not cleaned:
            return DiagnosticResult(
                category="Empty Input",
                source=source,
                language="Unknown",
                severity="Warning",
                original_error="[No error text provided]",
                explanation="No error message was provided for analysis.",
                suggested_action=(
                    "Paste an error message from your terminal, IDE, or compiler."
                ),
                timestamp=timestamp,
            )

        language = self._detect_language(cleaned)

        # Current backend accepts C, Python and Java.
        if language == "cpp":
            result = DiagnosticResult(
                category="Unsupported Language",
                source=source,
                language="C++",
                severity="Warning",
                original_error=cleaned,
                explanation=(
                    "The current ErrorXplain backend accepts C, Python and Java "
                    "for offline rule processing. C++ is reserved in the API "
                    "but is not currently supported by the backend."
                ),
                suggested_action=(
                    "Use a C, Python or Java diagnostic for the current backend, "
                    "or add C++ support to the team engine."
                ),
                timestamp=timestamp,
            )

            self.history.insert(0, result)
            return result

        try:
            api_result = self._post_explain(cleaned, language)

            result = DiagnosticResult(
                category=api_result.get("category", "Unknown"),
                source=source,
                language=api_result.get("language", language),
                severity=self._map_severity(
                    api_result.get("severity", "Medium")
                ),
                original_error=cleaned,
                explanation=api_result.get(
                    "explanation",
                    "No explanation returned by the engine."
                ),
                suggested_action=api_result.get(
                    "suggestion",
                    "No corrective action returned by the engine."
                ),
                timestamp=timestamp,
            )

        except HTTPError as exc:
            result = DiagnosticResult(
                category="Backend Error",
                source=source,
                language=language,
                severity="Error",
                original_error=cleaned,
                explanation=(
                    f"The ErrorXplain backend rejected the request "
                    f"(HTTP {exc.code})."
                ),
                suggested_action=(
                    "Check the backend terminal for the request error "
                    "and verify the selected language is supported."
                ),
                timestamp=timestamp,
            )

        except (URLError, TimeoutError, OSError):
            result = DiagnosticResult(
                category="Engine Unavailable",
                source=source,
                language=language,
                severity="Error",
                original_error=cleaned,
                explanation=(
                    "The ErrorXplain backend could not be reached."
                ),
                suggested_action=(
                    "Start the FastAPI engine with "
                    "'uvicorn main:app --reload' and try again."
                ),
                timestamp=timestamp,
            )

        except Exception as exc:
            result = DiagnosticResult(
                category="Engine Error",
                source=source,
                language=language,
                severity="Error",
                original_error=cleaned,
                explanation=(
                    "An unexpected error occurred while contacting "
                    "the diagnostic engine."
                ),
                suggested_action=(
                    f"Check the backend terminal. Details: {exc}"
                ),
                timestamp=timestamp,
            )

        self.history.insert(0, result)
        return result

    def get_sample_errors(self) -> Dict[str, str]:
        """
        Samples retained for the existing desktop UI.

        These are UI demonstration inputs and are independent of
        the backend's rule list.
        """
        return {
            "C Syntax Error": (
                "main.c:5:9: error: expected ';' before return"
            ),
            "Python Runtime Error": (
                "Traceback (most recent call last):\n"
                '  File "calculator.py", line 42, in compute_average\n'
                "    return sum(values) / len(values)\n"
                "ZeroDivisionError: division by zero"
            ),
            "Java Error": (
                "Main.java:10: error: cannot find symbol"
            ),
        }

    def get_history(self) -> List[DiagnosticResult]:
        return self.history

    def clear_history(self) -> None:
        self.history.clear()

    def report_unknown_error(
        self,
        raw_text: str,
        language: str,
        compiler_info: str,
        notes: str,
    ) -> Dict[str, str]:

        report = {
            "id": f"ERR-{len(self.feedback_queue) + 1:04d}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raw_text": raw_text.strip(),
            "language": language,
            "compiler_info": compiler_info.strip(),
            "notes": notes.strip(),
            "status": "Queued locally (Offline mode)",
        }

        self.feedback_queue.append(report)
        return report