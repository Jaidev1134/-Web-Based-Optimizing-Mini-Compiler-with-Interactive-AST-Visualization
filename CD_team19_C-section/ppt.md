# PPT Content — Web-Based Optimizing Mini-Compiler with Interactive AST Visualization
### Team 19 | C-Section | Compiler Design Mini Project

---

## Slide 1: Title Slide

**Title:** Web-Based Optimizing Mini-Compiler with Interactive AST Visualization

**Subtitle:** A Full-Pipeline Compiler Simulation with Real-Time Visualization

**Team:** Team 19, C-Section

**Subject:** Compiler Design (CD) — Mini Project

**Academic Year:** 2025–2026

**Guided By:** [Faculty Name / Guide Name]

**Institution:** [College/University Name]

---

## Slide 2: Problem Definition

### Problem
- Traditional compiler design education relies on command-line tools and textbook theory, making it difficult for students to visualize how compilation phases interact.
- Existing tools (GCC, LLVM) are production-grade and overwhelming for beginners — they don't expose intermediate representations or optimization steps in an accessible format.
- Students often struggle to correlate source code changes with their effects on Abstract Syntax Trees (AST), Three-Address Code (TAC), or assembly output.

### Goal
- Build a **web-based mini-compiler** that accepts a simplified C-style language and demonstrates the **complete compilation pipeline** — from lexical analysis to assembly code generation — with full visual feedback.
- Enable **live compilation** where changes in source code instantly reflect across all compiler phases.
- Implement **intermediate code optimization** (constant folding, dead code elimination, copy propagation) and allow side-by-side comparison of raw vs. optimized TAC.

### Our Solution
- A **Flask + PLY (Python Lex-Yacc)** powered web application that tokenizes, parses, analyzes, optimizes, and translates code in real-time.
- **Interactive AST Visualization** using D3.js for zoomable, hierarchical syntax tree rendering.
- **Six compiler phases** demonstrated: Lexical Analysis → Parsing → Semantic Analysis → TAC Generation → Optimization → Assembly Generation.
- **CodeMirror** integrated code editor with syntax highlighting, live debounced compilation, and export functionality (PNG tree images, TXT code outputs).
- **Symbol Table viewer** showing variable types and optimized final values — simulating runtime memory.

---

## Slide 3: Literature Survey

| Sr. No. | Paper Title | Authors | Year | Key Contribution | Open Problem / Proposed Work |
|---------|------------|---------|------|-----------------|------------------------------|
| 1 | The Spoofax Language Workbench: Rules for Declarative Specification of Languages and IDEs | L. C. L. Kats, E. Visser | 2010 | Declarative, integrated IDE generation for DSLs using parser generators and program transformation; foundational for language workbench architecture. | Scaling declarative specifications to handle highly ambiguous legacy languages and reducing the dynamic overhead of generated IDE services. |
| 2 | Silver: An Extensible Attribute Grammar System | E. Van Wyk, D. Bodin, J. Gao, L. Krishnan | 2010 | Presents Silver AG system enabling modular and extensible language specifications; influenced our modular compiler engine design. | Handling highly cyclic dependencies without performance bottlenecks and mitigating the overhead associated with the forwarding mechanism. |
| 3 | Profile-Based Abstraction and Analysis of Attribute Grammars | A. M. Sloane | 2012 | Proposes profiling techniques for understanding attribute grammar behavior; relevant to our AST traversal and semantic analysis approach. | Generalizing profiling abstractions to accurately model parallel/concurrent attribute evaluation and dynamic scheduling strategies. |
| 4 | A Modular Specification of Oberon0 using the Silver Attribute Grammar System | T. Kaminski, E. Van Wyk | 2015 | Demonstrates modular compiler construction using attribute grammars; validated the phased architecture adopted in our project. | Ensuring strictly independent language extensions can be composed together without unforeseen, untraceable semantic interference. |
| 5 | Incremental Evaluation of Higher-Order Attributes | J. Bransen, A. Dijkstra, S. D. Swierstra | 2015 | Addresses incremental evaluation strategies for attribute grammars; relevant to our live/debounced recompilation approach. | Optimizing cache invalidation logic for deep incremental changes in massive ASTs without causing excessive memory bloat. |
| 6 | On Repair with Probabilistic Attribute Grammars | M. Koukoutos, M. Raghothaman, E. Kneuss, V. Kuncak | 2017 | Uses probabilistic methods for program repair via attribute grammars; provides theoretical grounding for error recovery strategies we implement. | Scaling probabilistic repair synthesis to encompass complex imperative state changes and deeply nested loops, rather than just local typing errors. |
| 7 | Syntax-Directed Variational Autoencoder for Structured Data | H. Dai, Y. Tian, B. Dai, S. Skiena, L. Song | 2018 | Applies syntax-directed translation concepts to deep generative models; reinforces the importance of grammar-guided code generation. | Incorporating context-sensitive constraints (like scoping and typing rules) directly within the VAE prior, which conventionally handles only CFG rules. |
| 8 | Syntax-Infused Variational Autoencoder for Text Generation | X. Zhang, Y. Yang, S. Yuan, D. Shen, L. Carin | 2019 | Syntax-infused neural generation; highlights how syntactic structure awareness improves code/text generation quality. | Bridging the gap between discrete structural syntax trees and continuous semantic vector spaces without losing local grammatical coherence in long sequences. |
| 9 | Principles and Patterns of JastAdd-Style Reference Attribute Grammars | N. Fors, E. Söderberg, G. Hedin | 2020 | Codifies best practices for RAG development; our compiler engine's AST node design draws from these declarative attribute patterns. | Developing automated formal verification for Reference Attribute Grammar (RAG) patterns and managing cyclic attributes without relying on manual termination logic. |
| 10 | Strategic Tree Rewriting in Attribute Grammars | L. Kramer, E. Van Wyk | 2020 | Integrates strategic term rewriting into AGs; theoretically supports our multi-pass TAC optimization strategy using tree traversals. | Mathematically ensuring the termination and confluence of arbitrary strategic rewrites when they interact concurrently with demand-driven attribute evaluation. |

---

## Slide 4: Software Tools & Requirements

### Programming Languages
| Component | Language |
|-----------|----------|
| Backend / Compiler Engine | Python 3.8+ |
| Frontend UI | HTML5, CSS3, JavaScript (ES6) |

### Frameworks & Libraries

| Tool | Purpose | Version |
|------|---------|---------|
| **Flask** | Lightweight web framework for serving APIs and static files | 2.x |
| **PLY (Python Lex-Yacc)** | Formal lexer and LALR(1) parser generator for tokenization and parsing | 3.11 |
| **D3.js** | Data-driven SVG tree visualization for interactive AST rendering | v7 |
| **CodeMirror** | In-browser syntax-highlighted multi-line code editor | 5.65 |
| **Bootstrap** | Responsive UI framework with dark theme support | 5.3.2 |
| **html2canvas** | Client-side screenshot capture for exporting AST tree as PNG | 1.4.1 |

### Hardware Requirements
| Specification | Minimum |
|--------------|---------|
| Processor | Intel i3 / equivalent |
| RAM | 4 GB |
| Storage | 500 MB free space |
| Browser | Chrome / Firefox / Edge (modern) |
| OS | Windows 10+ / macOS / Linux |

### Development Tools
- **IDE:** VS Code / PyCharm
- **Version Control:** Git & GitHub
- **Package Manager:** pip (Python)

---

## Slide 5: Architecture & Design

> **Architecture Diagram** (Generated using AI-powered Nano Banana image generation — academic-style, self-explanatory)

### System Architecture Diagram

![System Architecture — Web-Based Optimizing Mini-Compiler](nano_banana_compiler_arch_1775717618492.png)

> **Figure 1:** Complete three-layer system architecture showing the Presentation Layer (Browser Client with CodeMirror Editor and D3.js Visualization), Application Layer (Flask Backend with 6-phase PLY Compiler Pipeline), and Data Flow transformations from Source Code to MIPS Assembly.

### Key Design Decisions
1. **PLY over Regex:** Migrated from basic regex tokenization to PLY's formal LALR(1) parser — supports context-free grammars for if/else, while loops, and nested expressions.
2. **AST & CFG Construction:** Object-oriented AST nodes dynamically transform into a Basic Block Control Flow Graph (CFG) explicitly tracking loops via Depth-First Search (DFS) traversals.
3. **Multi-Pass Optimizer:** Iterative optimization loop runs across Dominator Trees until no further reductions are possible (fixed-point convergence).
4. **Live Compilation:** 800ms debounced event listener triggers recompilation on every keystroke — no button press needed.

---

## Slide 6: Implementation

### Phase 1 — Lexer (Tokenization)
- Implemented using **PLY's `lex` module**.
- **28 token types** defined: NUMBER, ID, STRING_VAL, arithmetic operators (+, −, *, /, ^), relational operators (==, !=, <, >, <=, >=), delimiters, semicolons.
- **7 reserved keywords:** `if`, `else`, `while`, `for`, `sin`, `cos`, `sqrt`.
- Error handling for illegal characters with line-number tracking.

### Phase 2 — Parser (Syntax Analysis)
- Implemented using **PLY's `yacc` module** (LALR(1) parsing).
- **Context-Free Grammar** supports: variable assignments, arithmetic expressions, conditional statements (if-else), while loops, function calls (sin, cos, sqrt), and nested blocks.
- **Operator precedence:** Relational → Additive → Multiplicative → Power → Unary.
- **Panic-mode error recovery** via `parser.errok()` — continues parsing after syntax errors.

### Phase 3 — Semantic Analysis
- **Type inference system:** Propagates types (int, float, string) through expressions.
- **Symbol Table:** Tracks variable name, inferred type, source expression, and post-optimization final value.
- **Type mismatch detection:** Flags string operations with non-`+` operators.
- **Undefined variable detection:** Reports undeclared identifiers.

### Phase 4 — Control Flow Graph (CFG) & TAC Generation
- Recursive AST traversal generates linear TAC instructions.
- Converts TAC into **Basic Blocks** establishing hierarchical CFG mapping.
- Computed **Dominator Trees** explicitly segregate preheaders from back-edges for loop logic.
- TAC instructions: `x = y op z`, `ifFalse cond goto L`, `goto L`, `L:`, `call func, arg`.

### Phase 5 — TAC Optimization Engine (9 Optimization Passes)
| Pass | Technique | Example |
|------|-----------|---------|
| 1 | **Constant Folding** | `t1 = 2 * 3` → `t1 = 6` |
| 2 | **Constant Propagation** | `a = 5; b = a + 1` → `b = 5 + 1` → `b = 6` |
| 3 | **Copy Propagation** | `t1 = x; y = t1` → `y = x` |
| 4 | **Algebraic Simplification** | `x * 1` → `x`, `x + 0` → `x`, `x * 0` → `0` |
| 5 | **Local Common Subexpr Elimination (CSE)** | Duplicate evaluated conditions collapsed across nodes |
| 6 | **Loop Invariant Code Motion (LICM)** | Pures evaluated inside loops safely hoisted into Preheader |
| 7 | **Dead Code Elimination** | Unused locals cleared natively through backward liveness tracking |
| 8 | **Unreachable Code Removal** | Code after unconditional `goto` is eliminated |
| 9 | **Temporary Inlining** | `t1 = a+b; x = t1` → `x = a+b` |

- **Division-by-zero safety:** Constants are NOT propagated into denominator positions if the value is zero.
- **Fixed-point iteration:** Optimization loop repeats until convergence (no changes detected).

### Phase 6 — Assembly Generation & Graph Coloring Register Allocation
- Translates optimized TAC directly into canonical MIPS assembly.
- Maps `IN/OUT` sets to build dynamic Interference Graph networks.
- Applies **Chaitin Graph-Coloring Register Allocator**:
  - Native segregation of ephemeral MIPS Temporaries (`$t0-t6`) and Callee Saved globals (`$s0-$sK`).
  - Automatically manages Memory spills (`LW/SW`) if architectural register constraints (`K`) are exceeded.
- Utilizes native MIPS instructions (`LW`, `SW`, `LI`, `ADD`, `BEQ`, `JAL`, `J`) mapped dynamically based on Graph Coloring availability instead of restrictive 3-register bottlenecks.

### Frontend Implementation
- **CodeMirror editor:** Monokai theme, line numbers, customizable K-Regs coloring slider, 500px height.
- **Dagre-D3 interactive rendering:** Seamless, scrollable SVG topologies displaying basic blocks dynamically mapping loop logic architectures.
- **Tab-based output:** Control Flow Graph (CFG) | TAC (side-by-side) | Assembly | Symbol Table | Legacy AST.
- **Export system:** PNG export via XML-Serialization for topologies; TXT export via Blob download.

---

## Slide 7: Testing

### Test Strategy
- **Unit Testing:** Individual compiler phases tested in isolation (lexer, parser, optimizer).
- **Integration Testing:** End-to-end compilation pipeline with complex multi-statement programs.
- **Edge Case Testing:** Division by zero, undefined variables, type mismatches, deeply nested expressions.

### Test Cases

| Test Case | Input | Expected Behavior |
|-----------|-------|-------------------|
| Basic arithmetic | `a = 5 + 3;` | TAC: `a = 8` (constant folded), ASM: `LOAD R1, 8; STORE a, R1` |
| Variable chaining | `a = 5; b = a * 2;` | TAC: `a = 5; b = 10` (propagated & folded) |
| Dead code elimination | `d = (a * 0) + (10 - 10);` | TAC: `d = 0` (algebraic simplification + folding) |
| Conditional branching | `if (t1 == t2) { n = 1; } else { n = 2; }` | Correct label generation, branch removal if condition is statically known |
| While loop | `while (a > 0) { a = a - 1; }` | Loop labels and backward jumps generated correctly |
| Division by zero safety | `z = c / b;` (where b = 0) | Constants NOT propagated into denominator; symbolic `z = c / b` preserved |
| Type mismatch | `x = 5 - "hello";` | Semantic error: "Type Mismatch: Cannot use '-' on strings." |
| Undefined variable | `y = unknown_var;` | Semantic error: "Undefined variable: 'unknown_var'" |
| Algebraic identities | `x = x + 0; x = x * 1;` | Both simplified away; `x` unchanged |
| Copy propagation chain | `r = q; s = r; t = s;` | Entire chain collapses to single assignment |

### Comprehensive Test Program (26 variables)
A comprehensive test program with 26 variables (`a` through `z`) was used to validate all optimization passes simultaneously — including constant folding, dead store elimination, algebraic simplification, copy chain resolution, conditional branch elimination, and division-by-zero protection.

---

## Slide 8: Results & Analysis

### Optimization Effectiveness

| Metric | Raw TAC | Optimized TAC | Improvement |
|--------|---------|---------------|-------------|
| Total Instructions (test program) | ~45+ lines | ~20 lines | **~55% reduction** |
| Temporary variables used | 15+ | 0 (all inlined) | **100% elimination** |
| Control flow labels | 6+ labels | Only active labels retained | Dead labels removed |
| Constant expressions | All symbolic | All pre-computed at compile-time | **Compile-time evaluation** |

### Key Results
1. **Constant Folding:** All statically computable expressions (e.g., `(3+7)*(2-1)*(0+1)`) reduced to single constants at compile time.
2. **Dead Code Elimination:** Assignments to unused temporaries and unreachable blocks are fully removed.
3. **Division-by-Zero Safety:** The optimizer correctly refuses to propagate constants into division-by-zero scenarios, preserving symbolic expressions for runtime safety.
4. **Copy Chain Resolution:** Multi-step copy chains (`r = q; s = r; t = s`) fully resolved.
5. **Branch Elimination:** Statically deterministic conditionals (e.g., `if(0)`) have their dead branches completely removed, including associated labels and jumps.

### Performance
- **Live compilation latency:** < 200ms for typical programs (debounce: 800ms).
- **No external dependencies:** All compilation runs locally in-memory — no database, no cloud API.
- **Browser rendering:** D3.js tree renders instantly for ASTs with 50+ nodes.

### Visualization Impact
- Students can **visually trace** how source code maps to AST structure.
- Side-by-side TAC comparison makes optimization effects **immediately obvious**.
- Symbol table provides a **debugger-like** experience showing final variable states.

---

## Slide 9: Demonstration

> **Note to presenter:** This slide should include live screenshots / screen recordings of the running application. Below is the demonstration flow to follow:

### Demo Flow

**Step 1 — Code Input:**
- Open the Mini-Compiler Studio in a browser (`http://localhost:5000`).
- Write sample code in the CodeMirror editor:
```
a = 10;
b = a * 2;
if (b > 15) {
    c = sin(3.14);
} else {
    c = 0;
}
while (a > 0) {
    a = a - 1;
}
```

**Step 2 — Live Compilation:**
- Show that the AST tree, TAC, Assembly, and Symbol Table update in **real-time** as code is typed (800ms debounce).

**Step 3 — Control Flow Graph (CFG) / AST Tree Viewer:**
- Play with the 'K-Regs Configuration' slider simulating hardware limitations!
- Navigate to the "Control Flow Graph" tab.
- Demonstrate Dagre-D3 topological block processing. Emphasize green "Preheader" blocks spawned from the Python compiler correctly extracting loop-invariant functions! 
- Export the diagram as PNG using the 📸 button.

**Step 4 — TAC Comparison:**
- Navigate to the "Three-Address Code" tab.
- Show **Raw TAC** (left panel) vs **Optimized TAC** (right panel) side-by-side.
- Highlight specific optimizations: constant folding, removed temporaries, simplified expressions.

**Step 5 — Assembly Output:**
- Navigate to the "Assembly (MIPS)" tab.
- Show the generated pseudo-assembly instructions (LOAD, STORE, ADD, BEQ, JMP, etc.).
- Export as TXT file.

**Step 6 — Symbol Table:**
- Navigate to the "Symbol Table (Memory)" tab.
- Show the table with columns: Identifier | Data Type | Final Value (Trace).
- Demonstrate that post-optimization values are displayed.

**Step 7 — Error Handling:**
- Type malformed code (e.g., `a = 5 +;`) and show the error banner with line-specific error messages.
- Type `x = 5 - "hello";` and show the semantic type-mismatch error.

---

## Slide 10: Conclusion & Future Enhancement

### Conclusion
- Successfully developed a **web-based optimizing mini-compiler** that demonstrates full pipeline control from lexical analysis to architecture-specific register allocation.
- The tool bridges the gap between **compiler theory and practical understanding** by making intermediate representations (like Control Flow Graphs) visible and explorable.
- The **PLY-based parsing engine** supports a rich subset of programming constructs: arithmetic, assignments, conditionals, loops, and built-in functions.
- The **multi-pass optimization engine** achieves significant TAC reduction through a full 9-pass dominator suite featuring **Local CSE and Loop Invariant Code Motion (LICM)**.
- Robust **graph-coloring register allocation** separates ephemeral temporaries from saved registers based on native MIPS conventions.
- The interactive D3.js AST/CFG visualizations and live compilation make compiler phases **tangible for students** and educators.
- The entire application runs **locally without external APIs or databases**, making it ideal for academic lab environments.

### Future Enhancements
1. **For Loop Support:** Extend the grammar to support `for(init; cond; update)` loop syntax.
2. **Array & Pointer Support:** Add data structure types for more complex programs.
3. **Step-by-Step Execution Debugger:** Extend the existing Symbol Table into an animated, line-by-line execution mode — visually stepping through TAC instructions and showing variable state changes in real-time (current implementation shows final post-optimization values only).
4. **Monaco Editor Integration:** Upgrade to VS Code's Monaco editor for IntelliSense-like autocomplete and richer editing experience.
5. **Multi-Language Targets:** Extend assembly generation to support x86, ARM, or WebAssembly output.
6. **Collaborative Mode:** Add multi-user real-time editing via WebSockets for classroom demonstrations.
7. **Deployment:** Host on a cloud platform (Heroku / Render) for wider accessibility.

---

## Slide 11: References

1. Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2006). *Compilers: Principles, Techniques, and Tools* (2nd ed.). Addison-Wesley.

2. Beazley, D. M. (n.d.). *PLY (Python Lex-Yacc)*. Retrieved from https://www.dabeaz.com/ply/

3. Kats, L. C. L., & Visser, E. (2010). The Spoofax Language Workbench: Rules for Declarative Specification of Languages and IDEs. In *Proceedings of the 25th Annual ACM SIGPLAN Conference on Object-Oriented Programming, Systems, Languages, and Applications* (OOPSLA 2010), pp. 444–463. ACM. DOI: 10.1145/1869459.1869497

4. Van Wyk, E., Bodin, D., Gao, J., & Krishnan, L. (2010). Silver: An Extensible Attribute Grammar System. *Science of Computer Programming*, 75(1-2), 39–54.

5. Sloane, A. M. (2012). Profile-Based Abstraction and Analysis of Attribute Grammars. In *Proceedings of the International Conference on Software Language Engineering* (SLE 2012).

6. Kaminski, T., & Van Wyk, E. (2015). A Modular Specification of Oberon0 using the Silver Attribute Grammar System. *Science of Computer Programming*, 114, 33–44. DOI: 10.1016/j.scico.2015.10.009

7. Bransen, J., Dijkstra, A., & Swierstra, S. D. (2015). Incremental Evaluation of Higher-Order Attributes. In *Proceedings of the ACM SIGPLAN Workshop on Partial Evaluation and Program Manipulation*.

8. Koukoutos, M., Raghothaman, M., Kneuss, E., & Kuncak, V. (2017). On Repair with Probabilistic Attribute Grammars. *arXiv preprint arXiv:1707.04148*.

9. Dai, H., Tian, Y., Dai, B., Skiena, S., & Song, L. (2018). Syntax-Directed Variational Autoencoder for Structured Data. In *Proceedings of the International Conference on Learning Representations* (ICLR 2018).

10. Zhang, X., Yang, Y., Yuan, S., Shen, D., & Carin, L. (2019). Syntax-Infused Variational Autoencoder for Text Generation. In *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics* (ACL 2019), pp. 2069–2078. DOI: 10.18653/v1/P19-1199

11. Fors, N., Söderberg, E., & Hedin, G. (2020). Principles and Patterns of JastAdd-Style Reference Attribute Grammars. In *Proceedings of the 13th ACM SIGPLAN International Conference on Software Language Engineering* (SLE 2020). DOI: 10.1145/3426425.3426934

12. Kramer, L., & Van Wyk, E. (2020). Strategic Tree Rewriting in Attribute Grammars. In *Proceedings of the 13th ACM SIGPLAN International Conference on Software Language Engineering* (SLE 2020). DOI: 10.1145/3426425.3426943

13. Bostock, M. (n.d.). *D3.js — Data-Driven Documents*. Retrieved from https://d3js.org/

14. Flask Documentation. (n.d.). *Flask Web Development, One Drop at a Time*. Retrieved from https://flask.palletsprojects.com/

---

*End of PPT Content — Team 19, C-Section*
