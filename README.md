# Mini-Compiler Studio

> A web-based educational compiler that takes C-style source code and walks it through the full compilation pipeline — lexing, parsing, semantic analysis, TAC generation, optimizations, register allocation — outputting MIPS assembly with live visualizations of the CFG and AST.

---

## Pipeline

```
Source Code
    │
    ▼
┌─────────────┐
│   LEXER     │  Tokenize into 28 token types
└─────────────┘
    │
    ▼
┌─────────────┐
│   PARSER    │  LALR(1) — builds AST
└─────────────┘
    │
    ▼
┌─────────────┐
│   SEMANTIC  │  Type inference + symbol table
└─────────────┘
    │
    ▼
┌─────────────┐
│  TAC GEN    │  Three-Address Code
└─────────────┘
    │
    ▼
┌─────────────┐
│ OPTIMIZE    │  9 passes — constant fold, CSE,
│             │  LICM, dead store, strength reduce…
└─────────────┘
    │
    ▼
┌─────────────┐
│    CFG      │  Basic blocks + dominator tree
└─────────────┘
    │
    ▼
┌─────────────┐
│  REG ALLOC  │  Chaitin graph-coloring (K-configurable)
└─────────────┘
    │
    ▼
┌─────────────┐
│   ASM GEN   │  MIPS-like assembly
└─────────────┘
```

---

## Project Structure

```
CD_team19_C-section/
├── README.md                  # This file
├── METHODOLOGY.md             # Full technical documentation
├── CD_team19_C-section/
│   ├── nanobanana_architecture_diagram.md
│   ├── improvement.md
│   └── ppt.md
└── code_team19_c-section/
    ├── app.py                 # Flask entry point (routes: /, /api/translate)
    ├── ply_compiler.py        # Core compiler (~1445 lines)
    │   ├── Lexer              # Tokenizer (28 token types)
    │   ├── Parser             # LALR(1) grammar
    │   ├── AST Nodes           # 11 node types
    │   ├── CompilerEngine     # Semantic analysis + TAC generation
    │   ├── ControlFlowGraph    # Basic blocks + dominators
    │   ├── LICMOptimizer      # Loop-Invariant Code Motion
    │   ├── TACOptimizer        # 9 optimization passes
    │   ├── GraphColoringAllocator  # Register allocation
    │   └── MIPSEmitter         # Assembly generation
    ├── static/
    │   ├── index.html          # UI (Bootstrap 5, CodeMirror, D3)
    │   ├── script.js           # Frontend logic
    │   └── style.css
    └── tests/
        ├── test_runner.py     # Full pipeline test (26 variables)
        ├── test_cse.py        # Common subexpression elimination
        ├── test_alloc.py      # Register allocation
        ├── test_interfere.py   # Liveness + interference graph
        └── test_licm.py       # LICM optimization
```

---

## How to Run

### Prerequisites

- Python 3.8+
- Flask
- PLY (`pip install ply`)

### Start the Server

```bash
cd code_team19_c-section
python app.py
```

Server starts at `http://localhost:5000`.

### Use the UI

1. Write C-style code in the editor (left panel)
2. Set `K` (number of registers, default: 4)
3. Click **Compile** or wait 800ms for auto-compile
4. Switch tabs to view: **CFG**, **AST**, **TAC**, **Assembly**, **Symbol Table**

### API

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"expr": "x = 5; y = x + 3;", "k_regs": 4}'
```

Returns: `tree`, `symbol_table`, `raw_tac`, `optimized_tac`, `assembly`, `cfg`, `errors`

---

## Supported Language

### Variables & Arithmetic
```
a = 5;
b = a * 2 + 3;
c = b - a / 2;
d = a ^ 2;         # power
```

### Control Flow
```
if (x < 5) {
    y = 1;
} else {
    y = 2;
}

while (n > 0) {
    n = n - 1;
}
```

### Built-in Math Functions
```
x = sin(y);
x = cos(y);
x = sqrt(z);
```

### Limitations
- No `for` loops (token exists, grammar rule missing)
- No user-defined functions
- No arrays or structs
- No type declarations (inferred from usage)
- No comments in source

---

## Optimization Passes (9 total)

| # | Pass | What it does |
|---|------|-------------|
| 1 | Constant Folding | `2 * 3` → `6` |
| 2 | Constant Propagation | `x = 5; y = x` → `y = 5` |
| 3 | Copy Propagation | `a = b; c = a` → `c = b` |
| 4 | Algebraic Simplification | `x + 0` → `x`, `x * 1` → `x`, `x * 0` → `0` |
| 5 | Local CSE | `a+b` computed twice → reuse result |
| 6 | LICM | Loop-invariant `sin(x)` hoisted out of loop |
| 7 | Dead Store Elimination | Remove unused variables (Safe Shielded) |
| 8 | Unreachable Code Removal | Remove code after unconditional `goto` |
| 9 | Strength Reduction | `x * 2` → `x + x`, `x ^ 2` → `x * x` |

**Stability Features**: 
- **Safe DSE Shield**: Ensures no variable used in control flow or future logic is prematurely pruned.
- **Assembler Safety**: Migrated scratch work from reserved `$at` to safe `$t7/$t6` registers.
- **Relational Completeness**: Native support for all operators: `==`, `!=`, `<`, `>`, `<=`, `>=`.

**Result: ~60% instruction reduction** with 100% semantic fidelity.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 · Flask 2.x · PLY 3.11 |
| Frontend | HTML5 · Bootstrap 5.3.2 · CodeMirror 5.65 |
| Visualization | D3.js v7 · dagre-d3 0.6.4 |
| Export | html2canvas 1.4.1 |

---

## Team

**Team 19 — C-Section**
Compiler Design Mini Project · 2026-2027
