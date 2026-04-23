# Project Improvements for Syntax Directed Translator

This document outlines the planned improvements to build upon the existing Compiler Design project (originally developed by senior team 19, C-section). The goal is to extend the current codebase into a more comprehensive mini-project by implementing more advanced compiler phases and enhancing the user experience.

*Acknowledgment: This project builds upon the foundational Syntax Directed Translation implementation created by our seniors (Team 19, C-section).*

---

## I. Planned Improvements (Original Scope)
These are the core improvements that have been identified to expand the existing tool:

1. **Syntax Error Highlighting and Recovery:** 
   - Implement robust error handling that highlights *exactly where* the syntax error occurred in the input (e.g., underlining the specific character).
   - Attempt "panic-mode" recovery to continue parsing rather than simply crashing.
2. **Conditional Statements & Loops:** 
   - Extend the grammar beyond simple mathematical expressions to support full programming statements like `if-else`, `while`, and `for` loops.
3. **Symbol Table and Variable Assignment:** 
   - Implement a working symbol table to track variable types, scopes, and memory locations. 
   - Support variable assignment flows (e.g., `x = 5 + 3; y = x * 2`).
4. **Additional Operators & Functions:** 
   - Parse and evaluate built-in functions such as `sin()`, `cos()`, `sqrt()`, as well as relational and logical operators (`&&`, `||`, `==`, `!=`, `<`, `>`).
5. **Export Capabilities:**
   - **Data Export:** Allow users to export the Abstract Syntax Trees (AST) and Three-Address Code (TAC) as downloadable files (JSON, txt, CSV) for offline analysis.
   - **Image Export:** Add a button to download the D3.js visual syntax tree as a high-quality SVG or PNG image.
6. **Full Compiler Simulation & Evaluator Module:** 
   - Expand the current simple numeric evaluator into a full interpreter that simulates the execution of code blocks across active variable environments.
7. **Optimization & Final Code Generation:** 
   - Integrate modules that apply optimizations to the generated TAC and output final machine/assembly code targets.

---

## II. Suggested New Architectural Features (For Mini-Project Expansion)
To take this project significantly further and demonstrate advanced concepts for your mini-project, I highly recommend adding these features:

### 1. Upgrade Parsing Engine (Lex / Yacc equivalent)
- **Current State:** The app uses basic Regex tokenization and a strict Shunting Yard algorithm (which only supports mathematical expressions).
- **Enhancement:** To support loops, conditionals, and statements, migrate the parsing engine to use a formal parser generator like **PLY (Python Lex-Yacc)** or build a formal **Recursive Descent Parser**. This aligns much closer to real-world Compiler Design curriculum.

### 2. Intermediate Code Optimization Visualizer
- **Current State:** TAC is generated but not manipulated.
- **Enhancement:** Implement an optimization phase and create a "before and after" UI tab. Visualise optimization passes such as:
  - **Constant Folding:** Automatically reducing `t1 = 2 * 3` to `t1 = 6`.
  - **Dead Code Elimination:** Identifying and removing unused variables.
  - **Common Subexpression Elimination:** Reusing calculations.

### 3. Semantic Analysis Phase (Type Checking)
- **Enhancement:** Introduce simple data types (Integer, Float, Boolean, String). Implement a type-checking phase that flags Type Mismatch Errors.
- If a user types `x = 5 + "hello"`, visually intercept and describe the semantic error in the frontend.

### 4. Interactive Code Editor & Live Feedback
- **Enhancement:** Replace the basic input `text` field with a mini code editor (like Monaco Editor or CodeMirror) to support multi-line scripts. 
- Implement live debounced requests so the GUI (Tree, TAC, and Steps) updates dynamically as you type, without needing to press the "Translate" button.

### 5. Live Memory / State Monitor
- **Enhancement:** During the Evaluation phase, create a visual "Memory Viewer" panel that updates in real-time as variables are assigned and calculated line-by-line, showing the internal state changing just like a debugger.

### 6. Assembly Code Target Viewer
- **Enhancement:** Add the final stage of compiler design: convert the Three-Address Code into readable Assembly language (e.g., MIPS32 or a basic x86 subset) to fully complete the pipeline simulated by the web app.

---

## III. Requirements & Tech Stack Evaluation

The architecture required for these upgrades relies solely on local processing. **No paid tools, subscriptions, or external web APIs are required.** 

### 1. External Tools and Subscriptions (None Needed)
- **Paid Tools:** None required.
- **Free Substitutes:** All features can be implemented using completely free, open-source libraries.
- **API Capabilities:** No external API keys (like OpenAI, AWS, Google Cloud) are needed. Compilation, syntax parsing, and AST generation run entirely locally within the Flask backend. 
- **Database Limits:** No persistent external database (SQL/NoSQL) is required. The Symbol Table and execution state will be securely held in memory (using Python dictionaries/JSON mapped to active sessions) during translation.

### 2. Recommended Open-Source Stack
- **Backend:** Python (v3.8+)
- **Parser Generator (Crucial):** [PLY (Python Lex-Yacc)](https://github.com/dabeaz/ply). Free and deeply integrated into standard Compiler Design curriculums. Use this instead of regex matching. *(Installation: `pip install ply`)*
- **Web App Framework:** Flask (Pre-existing/Free).
- **Code Editor Extension:** embed the free [CodeMirror](https://codemirror.net/) or [Monaco Editor](https://microsoft.github.io/monaco-editor/) web library for syntax-highlighted multi-line input.
- **Exporting Libraries:** Integrate `html2canvas` (Free JS Library) to natively snapshot and download the D3.js Tree as a PNG.

---

## IV. Complete Implementation Plan

Following this phased implementation limits breaking changes to the existing project while rolling out full compiler upgrades.

### Phase 1: Architecture & Lexer/Parser Overhaul (Weeks 1-2)
*Goal: Replace the limited Shunting Yard algorithm with a formal PLY compiler parser capable of reading conditionals and variable assignments.*
1. Install PLY (`pip install ply`).
2. Write `lexer.py` to tokenize data structures correctly — capturing data types, relational operators (`>`, `<`), logic constraints, and strings.
3. Write `parser.py` using PLY's `yacc`. Map context-free grammar to generate hierarchical Python nodes.
4. Replace the backend POST endpoint inside `app.py` to intercept requests through the new `parser.py` rather than traditional tokenization arrays. 

### Phase 2: AST Processing & Symbol Table (Week 3)
*Goal: Structuring data contextually so memory spaces can be simulated.*
1. Enhance the Python Node objects to store line references and value data.
2. Initialize a global `SymbolTable` dictionary.
3. Upon encountering assignment grammar (`x = 5`), execute backend logic that flags "x" as declared, stores its type (Integer), and pushes that to the `SymbolTable`.
4. Render an HTML Bootstrap Table (`#symbol-table`) that hits an API endpoint to retrieve and visually print this dynamic memory map.

### Phase 3: Semantic Analysis and Error Recovery (Week 4)
*Goal: Intelligent error feedback instead of terminal crashing.*
1. Map out "Panic Mode" triggers inside `yacc.py` to intercept Syntax errors. Instead of failing the application, push a formatted error string (`"Missing ';' at line 4"`) to the frontend alert banner.
2. Add Type-Checking during syntax traversal. If the AST finds an attempt to combine illegal objects (Integer + String), raise a Semantic Error payload to the UI.

### Phase 4: Intermediate Optimization (Week 5)
*Goal: Processing generated TAC for efficiencies.*
1. Run a loop across generated Three Address Code arrays in the backend. 
2. Implement "Constant Folding" functions to find instances where `t1 = 2 * 3` is calculated explicitly, replacing it with `t1 = 6`. 
3. Introduce a "Before/After" side-by-side div on the frontend HTML to compare "Raw TAC" and "Optimized TAC".

### Phase 5: GUI Enhancements and Export Functions (Week 6)
*Goal: Delivering a polished, production-ready mini-project product.*
1. Refactor `index.html` to inject a proper Javascript text editor (like CodeMirror) to allow easy multi-line coding instead of standard form inputs.
2. Develop standard vanilla JS File/Blob functions to allow users to export TAC outputs as `.txt`. Let users hit an "Export Image" button using `html2canvas` spanning the `#chart` Div. 
3. Perform final application testing and prepare final presentation/demo.
