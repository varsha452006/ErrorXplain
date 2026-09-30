# ErrorXplain: Translating Compiler Errors into Plain-Language Explanations

**Member 1 — Desktop UI (Phase 1 Prototype)**

ErrorXplain is a lightweight desktop application designed to translate complex compiler, interpreter, and runtime error messages into clear, beginner-friendly explanations with actionable remediation steps.

---

## 🚀 How to Run the Application

From the project root folder:

```powershell
python main.py
```

### Running the Automated UI Tests
A headless automated test suite is included to verify all UI controls, badge styling, dialog actions, and error parsing flows:

```powershell
python tests/test_ui.py
```

---

## 📁 Project Architecture & File Overview

```
ErrorXplain/
│
├── main.py                     # Application entry point (initializes Qt, DPI scaling, and MainWindow)
├── requirements.txt            # Python dependencies (PyQt5)
├── styles.py                   # Centralized design system (modern QSS stylesheet and severity badge helpers)
├── mock_engine.py              # Mock Rule Engine implementation (inherits from RuleEngineInterface)
│
├── core/                       # Neutral domain contracts & data models
│   ├── __init__.py
│   └── engine_interface.py    # DiagnosticResult data model & RuleEngineInterface abstract contract
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # Primary application UI (Header, Input Card, Latest Error Card, Action Bar)
│   └── dialogs.py              # Modal dialogs (ErrorHistoryDialog & ReportUnknownErrorDialog)
│
└── tests/
    └── test_ui.py              # Automated test suite (8/8 tests covering UI workflows & DI contract)
```

---

## 🎯 Key Features Implemented in Phase 1

1. **Header Area**
   - Application title (`ErrorXplain`) and tagline (*"Understand programming errors. Fix them faster."*).
   - Real-time offline indicator badge.

2. **Diagnostic Input Card**
   - Large multiline text input with instructional placeholder.
   - **Quick Sample Chips**: Instant buttons to test **C++ Syntax Errors**, **Python Runtime Errors**, and **C Linker Errors** in one click (ideal for project presentations).
   - "Clear Input" and prominent "Analyze Error" action buttons.

3. **Latest Error Section (7 Required Diagnostic Fields)**
   - **Error Category** badge (e.g. `Syntax Error`, `Zero Division`, `Linker Error`).
   - **Language** badge (e.g. `C++`, `Python`, `C / C++`).
   - **Severity** badge with visual color distinction:
     - 🔴 **ERROR**: Red badge (`#fee2e2` / `#b91c1c`)
     - 🟡 **WARNING**: Amber badge (`#fef3c7` / `#b45309`)
     - 🟣 **FATAL**: Purple/Maroon badge (`#fae8ff` / `#86198f`)
   - **Source** badge (e.g. `Manual Input`, `VS Code Extension`, `Terminal`).
   - **Original Diagnostic Message**: Dark monospace terminal-styled card with one-click "Copy" button.
   - **Plain-Language Explanation**: Card written in conversational English explaining the root cause.
   - **Suggested Corrective Action**: Actionable step-by-step remediation guidance.

4. **Action Area & Dialogs**
   - **Error History**: Opens a dialog listing session diagnostics with timestamps, interactive row selection, preview, and a *"Load into Main Window"* action.
   - **Clear**: Completely resets input and restores the results view to an empty placeholder state.
   - **Report Unknown Error**: Opens an offline feedback modal to record unparsed diagnostics into a local queue for Member 3.

5. **Future Team Integration & Dependency Injection**
   - The Desktop UI (`MainWindow`) depends purely on the abstract `RuleEngineInterface` defined in `mock_engine.py`, completely decoupled from concrete engine implementations.
   - `main.py` serves as the composition root, instantiating `MockRuleEngine()` and injecting it into `MainWindow(engine=engine)`.
   - When **Member 3 (Rule Engine)** delivers the real engine, they simply implement `RuleEngineInterface` and pass it to `MainWindow` in `main.py` without modifying any UI code.
