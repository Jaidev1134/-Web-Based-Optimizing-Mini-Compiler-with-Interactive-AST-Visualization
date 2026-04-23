# Methodology — Mini-Compiler Studio

> Complete technical documentation of the compilation pipeline. Every stage, every function, every algorithm explained so a new developer can understand and modify the codebase without reading source code.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Phase 1 — Lexical Analysis (Lexer)](#2-phase-1--lexical-analysis-lexer)
3. [Phase 2 — Syntax Analysis (Parser)](#3-phase-2--syntax-analysis-parser)
4. [Phase 3 — Semantic Analysis & TAC Generation](#4-phase-3--semantic-analysis--tac-generation)
5. [Phase 4 — Control Flow Graph](#5-phase-4--control-flow-graph)
6. [Phase 5 — Optimizations](#6-phase-5--optimizations)
7. [Phase 6 — Register Allocation](#6-phase-6--register-allocation)
8. [Phase 7 — Assembly Generation](#7-phase-7--assembly-generation)
9. [Frontend Architecture](#8-frontend-architecture)
10. [Complete Pipeline Flow](#9-complete-pipeline-flow)
11. [Limitations & Future Work](#10-limitations--future-work)

---

## 1. Overview

### What This Compiler Does

This project implements a **mini-compiler** for a simplified C-style language. It takes source code as input and produces MIPS-like assembly as output, while showing every intermediate step (tokens, AST, TAC, CFG) visually in a web interface.

### The Mini-Language

The compiler accepts a restricted subset of C:

```
// Variables (no declarations needed)
x = 5;
y = x + 3 * 2;

// Arithmetic: +, -, *, /, ^ (power)
z = x ^ 2;

// Comparisons: ==, !=, <, >, <=, >=
if (x < 10) { y = 1; } else { y = 0; }

// Loops
while (x > 0) { x = x - 1; }

// Built-in math functions
a = sin(b);
a = cos(b);
a = sqrt(c);
```

### What the Compiler Cannot Handle

- Variable declarations (`int x;` — use `x = 5;` instead)
- `for` loops (token defined, grammar rule missing)
- User-defined functions
- Arrays and structs
- Strings (parsed but not compiled to assembly)
- Comments

### Project Structure

```
ply_compiler.py   — All compiler logic (~1445 lines, single file)
app.py            — Flask web server
static/
  index.html      — Single-page UI
  script.js       — Frontend JavaScript
  style.css       — Styling
```

### How to Think About the Compiler

Think of compilation as a **translation pipeline**. Each stage takes the output of the previous stage and transforms it into a new representation:

```
Source Text → Tokens → AST → TAC → Optimized TAC → Assembly
             Stage 1  Stage 2  Stage 3   Stage 5      Stage 7
             (Lexer)  (Parser) (TAC Gen) (Optimize)   (ASM Gen)

             CFG built between Stage 3 and 5
             Register allocation between Stage 5 and 7
```

---

## 2. Phase 1 — Lexical Analysis (Lexer)

### Purpose

Convert raw source code text into a stream of **tokens**. The lexer is the first gate — it doesn't understand code structure, it just groups characters into meaningful symbols.

### Token Types (28 total)

| Category | Tokens |
|----------|--------|
| **Keywords** | `if`, `else`, `while`, `for`, `sin`, `cos`, `sqrt` |
| **Literals** | `NUMBER` (integers/floats), `STRING_VAL` (quoted strings), `ID` (identifiers) |
| **Operators** | `+`, `-`, `*`, `/`, `^`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `=` |
| **Delimiters** | `(`, `)`, `{`, `}`, `;`, `,` |

### How the Lexer Works

The lexer uses **PLY (Python Lex-Yacc)**. Each token is defined by a function named `t_<TOKEN_NAME>`. PLY automatically matches these patterns in the source text.

**Key functions in the Lexer:**

```
t_PLUS      → matches "+"
t_MINUS     → matches "-"
t_MULT      → matches "*"
t_DIV       → matches "/"
t_POW       → matches "^"
t_NUMBER    → matches \d+(\.\d+)?  (integer or float)
t_ID        → matches [a-zA-Z_][a-zA-Z0-9_]* (identifiers)
```

**Special handling for IDs:**
```python
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = keywords.get(t.value, 'ID')   # "if" → IF token, "x" → ID token
    return t
```

**Line number tracking:**
```python
def t_newline(t):
    r'\n+'
    lex.lineno += len(t.value)
```

**Error handling:**
```python
def t_error(t):
    parse_errors.append(f"Illegal character '{t.value[0]}' at line {lex.lineno}")
    t.lexer.skip(1)   # Skip the bad character and continue
```

### Lexer Output

Given input `x = 5 + 3;`, the lexer produces:

| Token | Type | Value | Line |
|-------|------|-------|------|
| `x` | ID | `x` | 1 |
| `=` | EQUALS | `=` | 1 |
| `5` | NUMBER | `5` | 1 |
| `+` | PLUS | `+` | 1 |
| `3` | NUMBER | `3` | 1 |
| `;` | SEMI | `;` | 1 |

### Limitations of the Lexer

- **No comments**: `// comment` → lexer tries to parse `//` as division, fails
- **No multi-character operators**: handled correctly (PLY supports multi-character via longest-match)
- **Single lookahead**: PLY uses maximal munch (longest match first)

---

## 3. Phase 2 — Syntax Analysis (Parser)

### Purpose

Convert the token stream into an **Abstract Syntax Tree (AST)** — a hierarchical tree representation that captures the grammatical structure of the program.

### Parsing Algorithm

The parser uses **LALR(1) parsing** via PLY's `yacc`. LALR is a deterministic bottom-up parser that builds the parse table from the grammar, then uses shift-reduce actions during parsing.

**Why LALR(1)?**
- Efficient: O(n) parse time for n tokens
- Powerful enough for most programming languages
- Handles left recursion naturally (which is what we want for statement lists)

### Grammar Rules

The grammar is written as Python docstrings in PLY. Here are all the rules:

```
program           : statement_list

statement_list    : statement
                   | statement_list statement

statement         : ID EQUALS expression SEMI       # Assignment
                   | expression SEMI                 # Expression statement
                   | IF LPAREN expression RPAREN block
                   | IF LPAREN expression RPAREN block ELSE block
                   | WHILE LPAREN expression RPAREN block

block             : LBRACE statement_list RBRACE
                   | statement                        # No braces = single statement

expression        : expression PLUS expression
                   | expression MINUS expression
                   | expression MULT expression
                   | expression DIV expression
                   | expression POW expression
                   | expression EQEQ expression
                   | expression NEQ expression
                   | expression LT expression
                   | expression GT expression
                   | expression LTE expression
                   | expression GTE expression
                   | MINUS expression %prec UMINUS   # Unary minus
                   | LPAREN expression RPAREN
                   | NUMBER
                   | STRING_VAL
                   | ID
                   | SIN LPAREN expression RPAREN
                   | COS LPAREN expression RPAREN
                   | SQRT LPAREN expression RPAREN
```

### Operator Precedence

The precedence is declared explicitly (lowest to highest):

| Precedence Level | Operators |
|-----------------|-----------|
| 1 (lowest) | `==`, `!=`, `<`, `>`, `<=`, `>=` (comparisons) |
| 2 | `+`, `-` (additive) |
| 3 | `*`, `/` (multiplicative) |
| 4 | `^` (power) |
| 5 (highest) | Unary minus |

PLY uses precedence rules to resolve shift-reduce conflicts. When the parser sees both a shift (reading the next token) and a reduce (applying a grammar rule), precedence rules decide.

### AST Node Types (11 classes)

Every grammar rule that produces a value creates an AST node. The nodes are simple Python classes with a `to_dict()` method that serializes them for the frontend.

| Node Class | Fields | Represents |
|-----------|--------|-----------|
| `Program` | `stmts` | Root — list of all statements |
| `Block` | `stmts` | Grouped statements inside `{}` |
| `Assign` | `id_val`, `expr` | Variable assignment: `x = expr` |
| `BinOp` | `op`, `left`, `right` | Binary operation: `left op right` |
| `UnaryOp` | `op`, `expr` | Unary minus: `-expr` |
| `FuncCall` | `func_name`, `args` | Built-in function call |
| `IfStmt` | `cond`, `true_block`, `false_block` | Conditional statement |
| `WhileStmt` | `cond`, `block` | While loop |
| `Num` | `val`, `type` | Numeric literal (`int` or `float`) |
| `StrVal` | `val` | String literal |
| `Identifier` | `name` | Variable reference |

### AST Example

Input:
```
x = 5;
y = x + 3;
```

AST:
```
Program
├── Assign(id_val="x", expr=Num(5))
└── Assign(id_val="y", expr=BinOp(+, Identifier("x"), Num(3)))
```

### How the Parser Builds AST

For each grammar rule, the parser function receives the values of its components (either tokens or results from child rules) and constructs the appropriate node:

```python
def p_assign(p):
    'statement : ID EQUALS expression SEMI'
    p[0] = Assign(id_val=p[1], expr=p[3])
```

`p[1]` is the ID token's value ("x"), `p[3]` is the expression node returned by the expression rule.

### Error Handling in Parser

```python
def p_error(p):
    if p:
        parse_errors.append(f"Syntax error at '{p.value}' on line {p.lineno}")
        parser.errok()    # Panic mode: recover and continue
    else:
        parse_errors.append("Syntax error at EOF")
```

**Panic mode recovery**: When an error occurs, `parser.errok()` tells PLY to discard the current state and try to resynchronize at the next token. This prevents the parser from crashing on the first error.

### Limitations of the Parser

- **No `for` loop**: `for` token exists but no grammar rule uses it
- **Limited to one statement per line**: Semicolons are required
- **No `else if` chain**: Grammar only supports `if-else`, not `else if`

---

## 4. Phase 3 — Semantic Analysis & TAC Generation

### Purpose

Two things happen in this phase:

1. **Semantic Analysis**: Check that the code makes logical sense (types match, variables are defined)
2. **TAC Generation**: Convert the AST into **Three-Address Code (TAC)** — a linear, simplified intermediate representation

### Semantic Analysis

#### Symbol Table

The compiler maintains a **symbol table** that records every variable encountered:

```python
symbol_table = {
    "x": {"type": "int", "expr": "5", "value": 5},
    "y": {"type": "int", "expr": "x + 3", "value": 8}
}
```

Each entry stores:
- `type`: Inferred data type (`int`, `float`, `string`)
- `expr`: The original expression as a string
- `value`: The final computed value (after optimization)

#### Type Inference Rules

| Node | Rule |
|------|------|
| `Num(n)` | If `n` has a decimal point → `float`, else → `int` |
| `StrVal` | Always `string` |
| `Identifier` | Look up in symbol table |
| `BinOp` | If either operand is `float` → `float`, else `int` |
| `FuncCall` | Always `float` (math functions return float) |

#### Semantic Checks

1. **Undefined variable**: If `Identifier` name not in symbol table → error
2. **Type mismatch**: If string used in arithmetic → error
3. **Division by zero**: Handled specially (see below)

### TAC Generation

#### What is TAC?

Three-Address Code is a simple intermediate representation where each instruction has at most three operands. It's called "three-address" because instructions look like:

```
t1 = a + b      # result = operand op operand
ifFalse x goto L # conditional jump
goto L          # unconditional jump
L:              # label
```

TAC is the bridge between the high-level AST and low-level assembly.

#### TAC Instruction Types

| Format | Description | Example |
|--------|-------------|---------|
| `x = y` | Copy | `t1 = a` |
| `x = y op z` | Binary operation | `t2 = t1 + 5` |
| `x = - y` | Unary negation | `t3 = - b` |
| `x = call func, y` | Function call | `t4 = call sin, x` |
| `ifFalse x goto L` | Conditional branch | `ifFalse t1 goto L2` |
| `goto L` | Unconditional jump | `goto L1` |
| `L:` | Label | `L2:` |

#### Code Generation by Node Type

**Num Node:**
```
No TAC generated.
Return the numeric value directly.
```

**Identifier Node:**
```
No TAC generated.
Return the identifier name directly.
```

**BinOp Node (Binary Operation):**
```
Input: BinOp(+, left=Identifier("x"), right=Num(3))

1. Generate TAC for left expression → result_l
2. Generate TAC for right expression → result_r
3. temp = next_temp()
4. Emit: temp = result_l + result_r
5. Return temp
```

**Assign Node:**
```
Input: Assign(id_val="y", expr=BinOp(+, ...))

1. Generate TAC for expr → result
2. Emit: id_val = result
3. Add to symbol table
```

**IfStmt Node:**
```
Input: IfStmt(cond, true_block, false_block)

1. Generate TAC for cond → t_cond
2. L_false = new_label()
3. L_end = new_label()
4. Emit: ifFalse t_cond goto L_false
5. Generate TAC for true_block
6. Emit: goto L_end
7. Emit: L_false:
8. Generate TAC for false_block (if exists)
9. Emit: L_end:
```

**WhileStmt Node:**
```
Input: WhileStmt(cond, block)

1. L_start = new_label()
2. L_end = new_label()
3. Emit: L_start:
4. Generate TAC for cond → t_cond
5. Emit: ifFalse t_cond goto L_end
6. Generate TAC for block
7. Emit: goto L_start
8. Emit: L_end:
```

### Division-by-Zero Handling

When generating TAC for `a / b`:
- If `b` is a **known zero constant** → emit symbolic `t = a / b` (don't evaluate)
- If `b` is a **known non-zero constant** → constant-fold: compute the result
- If `b` is a **variable** → emit normal TAC; runtime handles the zero case

This is a **deliberate safety decision**: we don't propagate constants into denominators because that would change program behavior.

### CompilerEngine Class

The entire semantic analysis and TAC generation lives in the `CompilerEngine` class:

```python
class CompilerEngine:
    def __init__(self):
        self.tac = []              # List of TAC instruction strings
        self.temp_count = 0        # Counter for temp variable names (t0, t1, ...)
        self.label_count = 0       # Counter for labels (L0, L1, ...)
        self.symbol_table = {}     # Variable metadata
        self.semantic_errors = []  # Collected errors
```

Key methods:

| Method | What it does |
|--------|-------------|
| `gen_temp()` | Returns `"t0"`, `"t1"`, … (incrementing counter) |
| `gen_label()` | Returns `"L0"`, `"L1"`, … (incrementing counter) |
| `analyze_and_gen(ast)` | Walks the AST, fills symbol table, generates TAC |
| `infer_type(node)` | Returns `int`, `float`, or `string` |
| `gen_binop(op, left, right)` | Generates TAC for a binary operation |
| `gen_if_stmt(node)` | Generates TAC for if-else |
| `gen_while_stmt(node)` | Generates TAC for while loop |

---

## 5. Phase 4 — Control Flow Graph

### Purpose

The **Control Flow Graph (CFG)** is a graph representation of all possible execution paths through the program. It structures the TAC into **basic blocks** — sequences of instructions with no jumps in or out except at the start and end.

### Why Build a CFG?

The CFG enables **loop-based optimizations** (specifically LICM — Loop-Invariant Code Motion). Without knowing which instructions belong to which loops, we couldn't safely move invariant code out of loops.

### Basic Blocks

A **basic block** is a maximal sequence of TAC instructions where:
- Execution always starts at the first instruction
- No jumps in (except from the previous block)
- No jumps out (except at the last instruction)

```python
class BasicBlock:
    id: str          # "B0", "B1", etc.
    tac: list        # List of TAC instruction strings
    preds: set       # Set of predecessor block IDs
    succs: set       # Set of successor block IDs
    dom: set         # Set of dominator block IDs
    idom: BasicBlock # Immediate dominator
```

### CFG Construction Algorithm

**Step 1: Find Leaders**
Leaders are the first instruction of each basic block. Three rules:

```
Rule 1: The first instruction is always a leader
Rule 2: Any instruction that is the target of a jump (goto L or ifFalse ... goto L) is a leader
Rule 3: Any instruction immediately following a conditional jump is a leader
```

**Step 2: Build Blocks**
Group consecutive instructions between leaders into blocks.

**Step 3: Connect Blocks**
```
Instruction type → Connections:
  goto L           → Connect current block → target block (L)
  ifFalse ... goto L → Connect current → target AND current → fallthrough (next block)
  no jump          → Connect current → fallthrough (next block)
```

### CFG Example

Source:
```
x = 5;
if (x < 10) {
    y = 1;
} else {
    y = 2;
}
z = x + y;
```

TAC:
```
t1 = x < 10
ifFalse t1 goto L2
y = 1
goto L3
L2:
y = 2
L3:
t2 = x + y
z = t2
```

CFG:
```
B0 (entry)
  ├── [t1 = x < 10] ──ifFalse──→ B1
  └── (fallthrough)             B1 (false block)
B1: [y = 2]                        └── [y = 2]
B2: [y = 1] ──goto L3──→ B3   B2 (true block)
B3: [t2 = x+y, z=t2]           ├── [y = 1] ──goto──→ B3
                               └── (fallthrough)
```

### Dominators

A block **A** dominates block **B** if every path from the entry to **B** must go through **A**.

**Algorithm (Iterative Fixed-Point):**
```
Initial:  D(Entry) = {Entry}
          D(n) = {n} ∪ (∩ of D(p) for all predecessors p of n)
Iterate: Until no changes
```

**Immediate Dominator (idom)**: The unique dominator that is closest to a block (excludes itself).

### Preheader Insertion

For loop optimization (LICM), we need to insert a **preheader** — a synthetic block that runs before the loop and can hold loop-invariant instructions.

**Algorithm:**
```
1. Find loop header (block H where a back-edge points to it)
2. Find all predecessors of H that are NOT inside the loop
3. Create a new block (Preheader) with: goto H
4. Redirect all non-loop predecessors to point to Preheader instead of H
5. Connect Preheader → H
```

---

## 6. Phase 5 — Optimizations

### Overview

Nine optimization passes run in a loop until no further changes occur (fixed-point iteration). Optimizations are split into **local** (within a basic block) and **global** (across blocks).

### Optimization Pass Order

```
Loop (until stable):
  1. Remove Useless Jumps
  2. Temporary Inlining
  3. Strength Reduction
  4. Forward Optimizations (constant fold, propagate, simplify)
  5. Local CSE
  6. Unreachable Code Removal
  7. Dead Store Elimination

Final cleanup:
  8. Remove Useless Jumps
  9. Remove Unused Labels

Then (CFG-based):
  10. Build CFG
  11. LICM
  12. Flatten CFG
  13. Final cleanup (1-9 again)
```

### Pass 1: Remove Useless Jumps

**What**: Removes `goto L` when `L` is the very next instruction.

```
Before:
    goto L1
    L1:
After:
    L1:
```

**Algorithm:**
```
For each TAC instruction at index i:
  If instruction is "goto L" and i+1 is "L:":
    Remove the goto
```

### Pass 2: Temporary Inlining

**What**: Eliminates temporary variables by substituting their values directly.

```
Before:
    t1 = a + b
    c = t1
After:
    c = a + b
```

**Algorithm:**
```
For each TAC instruction at index i:
  If instruction matches "tN = X" (temp = something):
    For each subsequent instruction j > i:
      Replace all occurrences of "tN" with "X" in instruction j
    Remove instruction i
```

**Constraint**: Only handles temps named `t` + digits, and only 3-part assignments.

### Pass 3: Strength Reduction

**What**: Replaces expensive operations with cheaper equivalents.

| Pattern | Before | After | Why |
|---------|--------|-------|-----|
| Multiply by 2 | `x * 2` | `x + x` | Addition is faster than multiplication |
| Power of 2 | `x ^ 2` | `x * x` | Multiplication is faster than power |
| Divide by 1 | `x / 1` | `x` | Identity |

**Constraint**: Only when `x` is not a numeric literal (otherwise constant folding handles it).

### Pass 4: Forward Optimizations

This is a large pass (~130 lines) that combines multiple sub-optimizations in a single traversal.

#### 4a: Constant Folding

**What**: Evaluates constant expressions at compile time.

```
t1 = 2 + 3      → t1 = 5
t2 = 10 * 2     → t2 = 20
t3 = 5 < 10     → t3 = 1
t4 = 0 == 0     → t4 = 1
t5 = - 5        → t5 = -5
```

**Algorithm:**
```
Parse each instruction into parts: ["t1", "=", "2", "+", "3"]
If all operands are numeric:
  Evaluate the expression using Python's eval
  Replace instruction with the result
```

**Division safety**: Does NOT fold `a / 0`. If denominator is zero, keep symbolic.

#### 4b: Constant Propagation

**What**: Replaces variable uses with their known constant values.

```
x = 5           → x = 5
y = x + 3       → y = 5 + 3   (then folded to y = 8)
z = y * 2       → z = 8 * 2   (then folded to z = 16)
```

**Algorithm (forward walk):**
```
Track a map: variable_name → known_constant_value
For each instruction:
  If it's a simple assignment "v = C" where C is a constant:
    Add v → C to the constant map
  If it uses a variable v that is in the constant map:
    Replace v with its constant value in the instruction
  If it assigns to v:
    Remove v from the constant map (it may have changed)
```

#### 4c: Copy Propagation

**What**: Follows chains of variable copies.

```
a = b           → a = b
c = a + 1       → c = b + 1
d = c           → d = b + 1
```

**Algorithm:**
```
Track aliases: a → b (meaning "a currently holds the value of b")
For each instruction "x = y":
  If y is in aliases:
    Replace y with aliases[y]
  If x is not a temp:
    Add alias x → aliases.get(y, y)
  If x appears on the right side elsewhere:
    Break the alias chain
```

#### 4d: Algebraic Simplification

**What**: Applies identity rules.

| Pattern | Simplified |
|---------|-----------|
| `x + 0` or `0 + x` | `x` |
| `x - 0` | `x` |
| `x * 1` or `1 * x` | `x` |
| `x / 1` | `x` |
| `x * 0` or `0 * x` | `0` |
| `x - x` | `0` |

#### 4e: Branch Elimination

**What**: Eliminates branches whose condition is known at compile time.

```
t1 = 0          → removed (unused assignment)
ifFalse t1 goto L2  → ifFalse 0 goto L2  → goto L2
```

### Pass 5: Local Common Subexpression Elimination (CSE)

**What**: Reuses the result of a previously computed expression instead of recomputing it.

```
Before:
    t1 = a + b      # First computation
    x = t1
    t2 = a + b      # Same expression!
    y = t2
After:
    t1 = a + b
    x = t1
    t2 = t1         # Reuse previous result
    y = t2
```

**Algorithm (canonical form for commutative ops):**
```
For each basic block:
  available = {}   # Maps canonical expression → result temp
  For each instruction:
    If it's "t = x op y" where op is commutative (+, *):
      canonical = sorted([x, y]) joined with op
      If canonical in available:
        Replace with "t = available[canonical]"  # Reuse
      Else:
        Add canonical → t to available
    If it redefines x or y:
      Remove from available (expression may have changed)
```

### Pass 6: Unreachable Code Elimination

**What**: Removes code that can never be executed.

```
goto L3
x = 5      # After unconditional goto — unreachable
L3:
y = 10
```

**Algorithm:**
```
1. Collect all labels targeted by any jump
2. Traverse TAC linearly, marking reachable instructions
3. Any instruction after an unconditional goto that isn't a label → unreachable
4. Remove unreachable instructions
5. Remove label definitions for labels not in the target set
```

### Pass 7: Dead Store Elimination

**What**: Removes assignments to variables that are never used afterward.

```
x = 5      # Dead if x is never read again
y = 10
```

**Algorithm (backward dataflow):**
```
1. Find all user variables (non-temp variables in symbol table)
2. Start with an empty "needed" set
3. Backward pass:
   - Labels and jumps always need the variables they reference
   - For "x = ...", mark x as needed if used in the right side
   - For "ifFalse x goto L", mark x as needed
4. Forward pass: any assignment to x where x is NOT in "needed" → remove
```

### Pass 8: Remove Unused Labels

**What**: Removes label definitions that nothing jumps to.

```
L1:              # Never targeted
x = 5
L2:
y = 10
```

### Pass 9: LICM (Loop-Invariant Code Motion)

**What**: Moves computations out of loops if their result doesn't depend on the loop iteration.

```
Before:
while (n > 0) {
    x = sin(3.14);    # sin(3.14) doesn't depend on n
    y = y + x;
    n = n - 1;
}

After:
t_hoist_1 = sin(3.14);   # Computed once, outside loop
while (n > 0) {
    x = t_hoist_1;        # Use the pre-computed value
    y = y + x;
    n = n - 1;
}
```

**LICM Algorithm:**

```
1. Identify loops:
   - Find all back-edges (H → H where H dominates the predecessor)
   - For each back-edge, the target is the loop header

2. For each loop:
   a. Find all blocks in the loop (predecessor traversal from header)
   b. Track variables assigned within the loop
   c. For each instruction in each loop block:
      - Check if it's pure (only sin/cos/sqrt calls — no side effects)
      - Check if all operands are loop-invariant:
        * Constants: always invariant
        * Variables assigned within loop: NOT invariant
        * Variables from outside loop: invariant
      - If invariant:
        * Create hoisted temp in preheader: t_hoist_N = original_expr
        * Replace the in-loop instruction with: x = t_hoist_N
```

**Hoisting details:**
```
In-loop instruction:  x = sin(3.14)
Preheader:            t_hoist_1 = sin(3.14)
In-loop (modified):   x = t_hoist_1
```

**Limitation**: LICM only handles pure function calls (sin, cos, sqrt). Assignments to user variables within loops are NOT moved, as they may have side effects or be used for loop termination.

---

## 6. Phase 6 — Register Allocation

### Purpose

The optimized TAC uses temporary variables (`t0`, `t1`, …). The register allocator maps these to a limited number of physical MIPS registers. If there aren't enough registers, it **spills** values to memory.

### The Problem

With K available registers and N temporary variables, if N > K, some variables must be stored in memory. The allocator must decide:
1. Which variables get registers
2. Which variables get spilled to memory
3. Where to insert load/store instructions

### Algorithm: Chaitin Graph Coloring

This is a simplified version of the Chaitin-Briggs algorithm used in real compilers.

**Step 1: Liveness Analysis**

Determine which variables are "live" (may be used in the future) at each point.

```
OUT[n] = USE[n] ∪ (IN[n+1] - DEF[n])

where:
  USE[n]  = variables used in instruction n (before being defined)
  DEF[n]  = variables defined in instruction n
  IN[n]   = variables live at entry to instruction n
  OUT[n]  = variables live at exit from instruction n
```

**Algorithm (backward pass):**
```
Initialize IN and OUT as empty sets
Repeat until no changes:
  For each instruction n (in reverse order):
    OUT[n] = union of IN of all successors
    IN[n]  = USE[n] union (OUT[n] minus DEF[n])
```

**Step 2: Build Interference Graph**

Two variables **interfere** if they are both live at some point.

```python
for each instruction n:
    for each d in DEF[n]:        # Variable being defined
        for each l in OUT[n]:    # Variable live at exit
            if d != l:
                add_edge(d, l)   # d and l interfere
```

Two variables that interfere cannot share the same register.

**Step 3: Graph Coloring (Simplified)**

**Phase 1 — Simplify (push to stack):**
```
While there exists an uncolored node with < K neighbors:
  Push node to stack (it can be colored later)
If all remaining nodes have ≥ K neighbors:
  Push the node with highest degree (most likely to spill)
```

**Phase 2 — Select (assign registers):**
```
While stack is not empty:
  Pop node n
  available_registers = all registers
  For each neighbor of n that is already colored:
    Remove neighbor's color from available_registers
  If available_registers is not empty:
    Assign any available register to n
  Else:
    Mark n as spilled
```

### Register Mapping

| Variable Type | MIPS Registers | Count |
|-------------|---------------|-------|
| Temp variables (`t0`-`t6`) | `$t0` - `$t6` | 7 |
| User variables (`$s0`-`$sK-1`) | `$s0` - `$s{k-1}` | K (user-configurable, default 4) |

**Why separate pools?**
- `$t0`-`$t6`: Callee-saved temporaries used during computation
- `$s0`-`$s{k-1}`: Callee-saved variables that persist across calls

### Spill Handling

If a variable is marked as spilled:
- **Store to memory**: When the variable's value is computed → `SW reg, variable`
- **Load from memory**: When the spilled variable is needed → `LW reg, variable`

The allocator inserts these load/store instructions around the instructions that use the spilled variable.

---

## 7. Phase 7 — Assembly Generation

### Purpose

Translate optimized TAC into **MIPS-like assembly language**. The output uses real MIPS register names and instruction mnemonics.

### MIPS Instruction Mapping

**Arithmetic:**

| TAC Operator | MIPS Instruction | Example |
|-------------|-----------------|---------|
| `+` | `ADD` | `ADD $s0, $t0, $t1` |
| `-` | `SUB` | `SUB $s0, $t0, $t1` |
| `*` | `MUL` | `MUL $s0, $t0, $t1` |
| `/` | `DIV` | `DIV $s0, $t0, $t1` |
| `<` | `SLT` | `SLT $t0, $s0, $s1` |
| `>` | `SGT` | `SGT $t0, $s0, $s1` |
| `==` | `SEQ` | `SEQ $t0, $s0, $s1` |
| `!=` | `SNE` | `SNE $t0, $s0, $s1` |

**Control Flow:**

| TAC | MIPS | Notes |
|-----|------|-------|
| `ifFalse x goto L` | `BEQ x, $zero, L` | Branch if x equals zero |
| `goto L` | `J L` | Unconditional jump |
| Label `L:` | `L:` | Same as TAC |

**Data Movement:**

| Situation | MIPS | Notes |
|-----------|------|-------|
| Load constant | `LI reg, value` | Load immediate |
| Load variable | `LW reg, var` | Load from memory |
| Store variable | `SW reg, var` | Store to memory |
| Register move | `MOVE dest, src` | Copy between registers |

### Assembly Generation by TAC Type

**Copy instruction (`x = y`):**
```
If y is a constant:
    LI $t0, 5
    SW $t0, x        (if x not in register)
    MOVE $sx, $ty    (if x and y both in registers)
If y is a variable:
    LW $t0, y
    SW $t0, x
```

**Binary operation (`t = x + y`):**
```
1. Get x into a register:    LOAD x into $tx
2. Get y into a register:    LOAD y into $ty
3. Compute:                   ADD $tz, $tx, $ty
4. Store result:             SW $tz, t
```

### Function Call Handling (Built-in Functions)

For `sin`, `cos`, `sqrt` — the compiler emits a placeholder comment:

```
t1 = call sin, x    → # sin(x) — runtime library call
```

In a production compiler, this would generate a `JAL` (jump and link) to a runtime function. The current implementation delegates to a runtime library.

---

## 8. Frontend Architecture

### Overview

Single-page Flask application. Backend serves `index.html`, frontend communicates via `/api/translate` POST endpoint.

### API Contract

**Request:**
```json
POST /api/translate
{
  "expr": "x = 5; y = x + 3;",
  "k_regs": 4
}
```

**Response:**
```json
{
  "tree": { "name": "Program", "children": [...] },
  "symbol_table": { "x": {"type": "int", "expr": "5", "value": 5}, ... },
  "raw_tac": ["x = 5", "y = 8"],
  "optimized_tac": ["x = 5", "y = 8"],
  "assembly": ["LI $t0, 5", "SW $t0, x", ...],
  "cfg": { "nodes": [...], "edges": [...] },
  "errors": []
}
```

### UI Tabs

| Tab | Content | Visualization |
|-----|---------|--------------|
| **CFG** | Basic blocks and control flow edges | dagre-d3 directed graph |
| **AST** | Hierarchical syntax tree | D3.js tree layout |
| **TAC** | Raw and optimized side-by-side | Plain text |
| **Assembly** | MIPS output | Amber monospace text |
| **Symbol Table** | Variables, types, values | Bootstrap striped table |

### Key Frontend Functions

| Function | Role |
|---------|------|
| `compile()` | POST to `/api/translate`, update all tabs |
| `drawCFG(cfgData)` | Render CFG using dagre-d3 (top-to-bottom layout) |
| `drawTree(treeData)` | Render AST using D3 tree layout |
| `downloadTxt(filename, text)` | Trigger file download |
| Export handlers | SVG → PNG via XMLSerializer + html2canvas |

### Auto-Compile

The editor has a `change` event handler debounced at 800ms:
- User types → 800ms silence → automatic compilation fires
- Prevents server overload from rapid typing
- Also triggers once on page load with example code

---

## 9. Complete Pipeline Flow

```
User Input (web UI or API)
         │
         ▼
┌────────────────────────────┐
│  Flask /api/translate      │  app.py
│  Receives: expr, k_regs    │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│  PLY Lexer                  │  ply_compiler.py:5-73
│  Tokenize source string     │
│  Output: Token stream       │
│  Errors: Illegal chars      │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│  PLY Yacc Parser            │  ply_compiler.py:164-265
│  LALR(1) parse              │
│  Output: AST (Program node) │
│  Errors: Syntax errors      │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│  CompilerEngine.analyze    │  ply_compiler.py:677-802
│  Semantic analysis          │
│  - Type inference           │
│  - Undefined var check      │
│  - Type mismatch check      │
│  TAC generation             │
│  - Walk AST recursively      │
│  - Emit TAC instructions    │
│  Output: raw TAC + symbol   │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│  Optimization Loop          │  ply_compiler.py:1145-1187
│  Until no change:           │
│  1. Remove useless jumps   │
│  2. Temporary inlining      │
│  3. Strength reduction      │
│  4. Forward opts (fold,    │
│     propagate, simplify)   │
│  5. Local CSE               │
│  6. Unreachable code        │
│  7. Dead store elimination  │
│  8. Remove unused labels   │
│  Output: optimized TAC      │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│  ControlFlowGraph.build     │  ply_compiler.py:270-439
│  - Find leaders              │
│  - Build basic blocks        │
│  - Connect with edges        │
│  - Compute dominators        │
│  - Insert preheaders         │
│  Output: CFG graph           │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│  LICMOptimizer.optimize     │  ply_compiler.py:441-533
│  - Identify loops            │
│  - Find loop-invariant code  │
│  - Hoist to preheader        │
│  Output: modified TAC       │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│  Flatten CFG to TAC         │
│  (depth-first traversal)    │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│  Final optimization sweep   │
│  (constant fold + cleanup)  │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│  GraphColoringAllocator     │  ply_compiler.py:535-653
│  - Liveness analysis (IN/OUT)│
│  - Build interference graph │
│  - Graph coloring (simplify │
│    + select)                 │
│  - Handle spills             │
│  Output: register map        │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│  MIPSEmitter.emit           │  ply_compiler.py:1189-1401
│  - Translate TAC to MIPS     │
│  - Map vars to registers     │
│  - Insert load/store for     │
│    spills                    │
│  Output: assembly list       │
└────────────────────────────┘
         │
         ▼
Flask returns JSON response
         │
         ▼
Frontend updates all tabs
```

---

## 10. Limitations & Future Work

### Current Limitations

| Limitation | Impact | Fix Difficulty |
|-----------|--------|---------------|
| No `for` loops | Limited loop syntax | Easy — add grammar rule |
| No user-defined functions | Can't build reusable code | Medium — add function def grammar, call stack management |
| No arrays/structs | Can't handle collections | Medium — add index expressions |
| No type declarations | Type inference only | Easy — add `int`, `float`, `string` keywords |
| No comments | Can't document source code | Easy — add `//` token rule |
| No `else if` chains | Nested conditionals only | Easy — recursive grammar |
| LICM only handles pure functions | sin/cos/sqrt only | Medium — track pure vs impure |
| No register spilling algorithm | Simple skip on spill | Medium — implement actual spill cost analysis |
| Limited operator support | No `+=`, `%=`, etc. | Easy — add tokens and grammar |
| Strings parsed but not compiled | `"hello"` can't produce output | Medium — add string handling to TAC |
| Single-pass optimization | Some optimizations missed | Medium — SSA form enables more |

### Planned Improvements (from `improvement.md`)

| Phase | Improvement |
|-------|------------|
| 1 | Global CSE across blocks using dominator tree |
| 2 | Register spilling with cost-based spill selection |
| 3 | Better loop analysis: induction variables |
| 4 | Better branch prediction hints in assembly |
| 5 | `for` loop support |
| 6 | Function call support with call stack |

---

## Quick Reference

### Class Map

| Class | File | Lines | Purpose |
|-------|------|-------|---------|
| `Lexer` | ply_compiler.py | 5-73 | Tokenization |
| `Program`, `Block`, `Assign`, etc. | ply_compiler.py | 75-162 | AST node types |
| `yacc` parser | ply_compiler.py | 164-265 | Grammar + AST construction |
| `BasicBlock` | ply_compiler.py | 270-275 | CFG block |
| `ControlFlowGraph` | ply_compiler.py | 276-439 | CFG construction + dominators |
| `LICMOptimizer` | ply_compiler.py | 441-533 | Loop-invariant code motion |
| `GraphColoringAllocator` | ply_compiler.py | 535-653 | Register allocation |
| `CompilerEngine` | ply_compiler.py | 677-802 | Semantic analysis + TAC generation |
| TAC optimization functions | ply_compiler.py | 804-1143 | Individual optimization passes |
| `optimize_tac` | ply_compiler.py | 1145-1187 | Optimization driver loop |
| `MIPSEmitter` | ply_compiler.py | 1189-1401 | Assembly generation |
| `compile_code` | ply_compiler.py | 1277-1444 | Main entry point |

### Variable Naming Conventions

| Pattern | Meaning | Example |
|---------|---------|---------|
| `t0`, `t1`, … | Compiler-generated temporary | `t0 = a + b` |
| `L0`, `L1`, … | Compiler-generated labels | `L0:` |
| `B0`, `B1`, … | Basic block IDs | CFG nodes |
| `$t0`-`$t6` | MIPS temp registers | Assembly |
| `$s0`-`$sK-1` | MIPS saved registers | Assembly |
