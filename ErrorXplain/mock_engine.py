"""
mock_engine.py
--------------
Mock Rule Engine & Diagnostic Adapter for ErrorXplain Desktop UI.

NOTE FOR TEAM INTEGRATION:
This module acts as the contract adapter between:
- Member 1 (Desktop UI)
- Member 3 (Error Parser + Rule Engine + Runtime Analysis)

When Member 3 delivers the real Rule Engine, this file or its methods
can be substituted with the real parsing service without touching the UI layer.
"""

from datetime import datetime
from typing import List, Dict, Optional
import re
from core.engine_interface import DiagnosticResult, RuleEngineInterface


class MockRuleEngine(RuleEngineInterface):
    """
    Mock implementation of Member 3's Rule Engine.
    Provides offline, heuristic-based mock analysis and history management.
    """

    def __init__(self):
        # Session history pre-populated with realistic examples for demo purposes
        self.history: List[DiagnosticResult] = [
            DiagnosticResult(
                category="Zero Division",
                source="Manual Input",
                language="Python",
                severity="Error",
                original_error='Traceback (most recent call last):\n  File "math_ops.py", line 18, in divide_numbers\n    return numerator / denominator\nZeroDivisionError: division by zero',
                explanation="The program tried to divide a number by 0, which is mathematically impossible in Python and crashes the program.",
                suggested_action="1. Add an `if denominator == 0:` guard check before performing the division.\n2. Handle edge cases or provide a fallback default value (e.g. return 0 or None).",
                timestamp="2026-09-18 19:15:20"
            ),
            DiagnosticResult(
                category="Syntax Error",
                source="VS Code Extension",
                language="C++",
                severity="Error",
                original_error="main.cpp:14:5: error: expected ';' before 'return'\n   14 |     return 0;\n      |     ^~~~~~",
                explanation="In C++, every statement must end with a semicolon (;). The compiler reached the 'return' statement on line 14 while still expecting a semicolon from the statement above it.",
                suggested_action="1. Check line 13 (the line right above line 14) in main.cpp.\n2. Make sure you put a semicolon `;` at the end of the previous statement.",
                timestamp="2026-09-18 19:28:44"
            )
        ]
        
        # Local feedback queue for unknown errors
        self.feedback_queue: List[Dict[str, str]] = []

    def get_sample_errors(self) -> Dict[str, str]:
        """Provides realistic sample errors for instant testing during presentations."""
        return {
            "C++ Syntax Error": (
                "main.cpp:14:5: error: expected ';' before 'return'\n"
                "   14 |     return 0;\n"
                "      |     ^~~~~~"
            ),
            "Python Runtime Error": (
                "Traceback (most recent call last):\n"
                '  File "calculator.py", line 42, in compute_average\n'
                "    return sum(values) / len(values)\n"
                "ZeroDivisionError: division by zero"
            ),
            "C Linker Error": (
                "/usr/bin/ld: /tmp/cc7qKpA3.o: in function 'main':\n"
                "solution.c:(.text+0x21): undefined reference to 'calculate_tax'\n"
                "collect2: error: ld returned 1 exit status"
            ),
            "Python Name Error": (
                "Traceback (most recent call last):\n"
                '  File "main.py", line 12, in <module>\n'
                "    print(user_name)\n"
                "NameError: name 'user_name' is not defined. Did you mean: 'username'?"
            )
        }

    def analyze(self, raw_text: str, source: str = "Manual Input") -> DiagnosticResult:
        """
        Translates a raw diagnostic string into an offline plain-language explanation.
        Uses pattern heuristics to simulate Member 3's real parser and rule engine.
        """
        cleaned = raw_text.strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not cleaned:
            return DiagnosticResult(
                category="Empty Input",
                source=source,
                language="Unknown",
                severity="Warning",
                original_error="[No error text provided]",
                explanation="No error message was provided for analysis. Please paste compiler or interpreter output into the text box.",
                suggested_action="Paste an error message from your terminal, IDE, or compiler output.",
                timestamp=timestamp
            )

        # 1. Check for Python Tracebacks and Exceptions
        if "Traceback" in cleaned or "ZeroDivisionError" in cleaned or "NameError" in cleaned or "TypeError" in cleaned or "IndexError" in cleaned or "IndentationError" in cleaned:
            lang = "Python"
            if "ZeroDivisionError" in cleaned:
                cat = "Zero Division"
                sev = "Error"
                exp = "The program tried to divide a number by 0, which is undefined in mathematics and causes Python to halt execution immediately."
                action = "• Add a conditional check before dividing (e.g., `if denominator != 0:`).\n• If calculating an average, check whether the list or container is empty first."
            elif "NameError" in cleaned:
                cat = "Name Resolution"
                sev = "Error"
                # Extract variable name if possible
                var_match = re.search(r"name '([^']+)' is not defined", cleaned)
                var_name = f"'{var_match.group(1)}'" if var_match else "the variable"
                exp = f"Python cannot find {var_name}. This happens when you try to use a variable before creating it, or when there is a typo in its spelling."
                action = f"• Verify the spelling of {var_name}.\n• Ensure you declared and assigned a value to {var_name} before using it.\n• If it is from another file or module, ensure you imported it at the top."
            elif "IndexError" in cleaned:
                cat = "Index Out of Bounds"
                sev = "Error"
                exp = "The program attempted to access an item at an index number that does not exist in the list or array (e.g., asking for item 5 in a list with only 3 items)."
                action = "• Remember that Python uses 0-based indexing (the first element is index 0).\n• Verify the list length with `len(my_list)` before indexing.\n• Check loop boundary conditions."
            elif "TypeError" in cleaned:
                cat = "Type Mismatch"
                sev = "Error"
                exp = "An operation was performed on incompatible data types, such as attempting to add a string and a number together or calling a non-function."
                action = "• Inspect the variables involved and check their types using `type(var)`.\n• Explicitly cast or convert types, e.g., `int(string_value)` or `str(number)`."
            else:
                cat = "Runtime Exception"
                sev = "Error"
                exp = "Python encountered an unhandled exception while running the code."
                action = "• Inspect the traceback line numbers to find where the error originated.\n• Consider wrapping fragile logic inside a `try...except` block."

        # 2. Check for C / C++ Compiler and Linker Errors
        elif "undefined reference" in cleaned or "ld returned 1 exit status" in cleaned:
            lang = "C / C++"
            cat = "Linker Error"
            sev = "Fatal"
            exp = "The compiler successfully translated your source code, but the linker cannot locate the actual definition/implementation of a function or variable you called."
            action = "1. Verify that the file containing the function's definition is included in your compile command (e.g. `gcc main.c utils.c -o app`).\n2. If using an external library (like math.h or pthread), make sure to link the flag (e.g., `-lm` or `-lpthread`).\n3. Check for typos between the function declaration in the header and its definition in the .c/.cpp file."

        elif "expected ';'" in cleaned or "error: expected" in cleaned:
            lang = "C++" if (".cpp" in cleaned or "std::" in cleaned or "cout" in cleaned) else "C"
            cat = "Syntax Error"
            sev = "Error"
            exp = "The compiler encountered an unexpected token because a previous statement or declaration was not properly closed with a semicolon (`;`)."
            action = "1. Look at the line mentioned in the error message and the immediate line preceding it.\n2. Add a semicolon `;` at the end of the statement right before where the error occurred."

        elif "was not declared in this scope" in cleaned or "undeclared identifier" in cleaned:
            lang = "C++" if "scope" in cleaned else "C"
            cat = "Undeclared Identifier"
            sev = "Error"
            exp = "You used a variable, function, or class name that the compiler has never seen in this file or scope."
            action = "1. Check for typos or capitalization mismatches.\n2. Ensure you have `#include`d the necessary header file (e.g., `<iostream>` or `<vector>`).\n3. If using the C++ standard library, remember to prefix with `std::` (e.g., `std::cout`) or write `using namespace std;`."

        elif "warning:" in cleaned.lower() and "error:" not in cleaned.lower():
            lang = "C / C++"
            cat = "Compiler Warning"
            sev = "Warning"
            exp = "The code compiled, but the compiler identified risky or non-idiomatic logic that may lead to bugs or undefined behavior at runtime."
            action = "• Review the warning details and resolve the underlying condition before running the program."

        elif "segmentation fault" in cleaned.lower() or "core dumped" in cleaned.lower():
            lang = "C / C++"
            cat = "Memory Access Violation"
            sev = "Fatal"
            exp = "A segmentation fault occurred at runtime. The operating system stopped the program because it attempted to read or write to restricted memory."
            action = "1. Check for null or uninitialized pointers being dereferenced (`*ptr`).\n2. Check for buffer overflows or out-of-bounds array access.\n3. Run your program through a debugger like `gdb` or `valgrind` to pinpoint the exact crashing line."

        # 3. Generic Diagnostic Fallback
        else:
            lang = "Auto-Detected"
            cat = "Diagnostic Message"
            sev = "Error" if ("error" in cleaned.lower() or "fail" in cleaned.lower()) else "Warning"
            exp = "ErrorXplain received a diagnostic message. The compiler or environment detected an issue preventing normal execution."
            action = "• Inspect the file and line number shown in the diagnostic message.\n• Verify variable declarations, syntax, and matching brackets or parentheses.\n• If this error is frequent, you can click 'Report Unknown Error' below to improve recognition."

        result = DiagnosticResult(
            category=cat,
            source=source,
            language=lang,
            severity=sev,
            original_error=cleaned,
            explanation=exp,
            suggested_action=action,
            timestamp=timestamp
        )

        # Append to session history (most recent first)
        self.history.insert(0, result)
        return result

    def get_history(self) -> List[DiagnosticResult]:
        """Returns the list of analyzed diagnostics."""
        return self.history

    def clear_history(self) -> None:
        """Clears the session history."""
        self.history.clear()

    def report_unknown_error(self, raw_text: str, language: str, compiler_info: str, notes: str) -> Dict[str, str]:
        """
        Stores an unparsed or misdiagnosed error report locally for offline storage.
        Simulates offline telemetry/feedback collection.
        """
        report = {
            "id": f"ERR-{len(self.feedback_queue) + 1:04d}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raw_text": raw_text.strip(),
            "language": language,
            "compiler_info": compiler_info.strip(),
            "notes": notes.strip(),
            "status": "Queued locally (Offline mode)"
        }
        self.feedback_queue.append(report)
        return report
