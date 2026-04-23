# Advanced Compiler Upgrades: Implementation Plan

The goal is to significantly enhance the mini-compiler by implementing realistic register allocation, advanced intermediate optimizations, and Control Flow Graph (CFG) visualization, adhering strictly to pedagogical and rigorous compiler design principles.

## Proposed Changes

### Phase 1: Architectural Refactoring & IR Invariants
Rather than a single monolithic optimization loop, we will decouple the optimization pipeline into formalized, sequential passes with clear input/output invariants. A master coordinator will loop through these passes until a fixed point (convergence) is reached.

#### 1. SSA-like Guarantees for Temporaries
- **Concept:** Establish a strict invariant that all compiler-generated temporary variables (`t1`, `t2`, etc.) adhere to single-assignment rules. 
- **Benefit:** Simplifies data-flow analysis, making CSE, LICM, and semantic reasoning drastically easier since the value of a temporary is immutable within its scope.

### Phase 2: Advanced Intermediate Optimizations

#### 1. Strength Reduction
- **Concept:** Replace expensive operations with logically equivalent cheaper ones.
- **Implementation:** Pattern match specific operators (e.g., `x * 2` → `x + x`, `x ** 2` → `x * x`, `x / 1` → `x`). Evaluated as an independent pass.

#### 2. Local Common Subexpression Elimination (CSE)
- **Concept:** Avoid recomputing identical math operations within Basic Blocks.
- **Implementation:** 
  - Canonicalize commutative expressions (e.g., `a + b` is treated identically to `b + a`) before hashing to maximize reuse.
  - Track `available_expressions` dictionary per Basic Block.
  - Clear invalidated expressions dynamically when constituent user variables are reassigned.

#### 3. CFG Normalization & Dominator Trees
- **Concept:** Transform linear TAC into a graph to reason about loops and structural flow.
- **Implementation:**
  - **Basic Blocks & Edges:** Build explicit directed edges (distinguishing fall-through vs. conditional branch edges).
  - **Dominator Tree Analysis:** Compute dominator sets for all blocks to strictly define loops and headers.
  - **Preheader Injection:** Explicitly mutate the CFG to insert loop preheader blocks before natural loops. This guarantees a safe insertion point for hoisted code.

#### 4. Loop-Invariant Code Motion (LICM)
- **Concept:** Move invariant computations out of loop bodies securely.
- **Implementation:**
  - Utilize Dominator Trees to accurately identify natural loops.
  - Check for invariants: operands are constants, or defined outside the loop.
  - Perform strict side-effect safety checks (ensure instructions hoisted don't cause faults like div-by-zero if the loop never executes, and ensure dominance properties aren't violated).
  - Hoist instructions to the explicitly generated loop preheader.

---

### Phase 3: Graph-Coloring Register Allocation
Replaces the naive memory-bound code generator with a realistic, hardware-constrained register allocation mechanism. We will simulate a limited environment of **4 general-purpose registers (e.g., R0-R3)** to guarantee spills in complex calculations for educational visibility.

#### 1. Instruction-Level Liveness Analysis
- Perform fine-grained Data-Flow Analysis computing `IN` and `OUT` sets at the individual instruction level, not just the basic block boundaries.
- Build highly accurate interference graphs showing exact variable overlap lifetimes.

#### 2. Interference Graph, Coalescing & Chaitin’s Graph Coloring
- Build the undirected interference graph.
- **Coalescing / Splitting:** Incorporate simplified live-range coalescing to eliminate redundant move instructions (e.g., merging nodes for `a = b` if their live ranges do not interfere). Support basic live-range splitting for variables spanning disconnected graph segments to reduce register pressure.
- **Spill Cost Estimation:** Instead of arbitrary spillage, prioritize spilling variables that are infrequently used or outside deep loops (using loop-nesting depth frequency multipliers).
- **Termination Guarantee:** Ensure iterative re-coloring safely bounds. If a spill fails to reduce register pressure sufficiently (e.g., spilling creates unavoidable temporary loads/stores that conflict), the algorithm falls back to an absolute memory-allocation mode for the offending node to break infinite coloring loops.

#### 4. Advanced Assembly Generation
- Utilize the computed Register Map. Translate TAC to MIPS pseudo-assembly mapping directly to `R0..R3`. 
- Only generate `LOAD`/`STORE` instructions when addressing explicit memory spills.

---

### Phase 4: Frontend Visualization Enhancements

#### 1. CFG Visualization (`script.js` & `index.html`)
- Integrate **Dagre-D3** for hierarchical directed graph visualization alongside the AST.
- Draw Basic Blocks as distinct rectangular nodes populated with their raw TAC.
- Use visual cues (e.g., red/dashed arrows for `ifFalse` branches, green/solid for fall-through/`goto` branches) to clarify CFG paths.

#### 2. Frontend Polish
- Introduce a "Configuration" toggle allowing users to change the Register count limit (e.g., 4 vs 32). This turns the platform into an experimental learning environment where users can visually observe the impact of hardware constraints on register spilling.

---

## Verification Plan

### Differential Testing & Generative Validation
- **Differential Execution Simulator:** Implement an automated mathematical engine running both "Raw TAC" and "Optimized TAC" in parallel. Assert that end-state variables map flawlessly.
- **Fuzzing / Symbolic Checks:** Extend the framework to randomly generate AST syntax trees or introduce high-entropy variable assignments and edge cases (divide by zero, negative powers). Ensures the compiler formally maintains semantic preservation regardless of AST shape.

### Manual Verification
- **CSE Canonicalization:** Input `x = a + b` and `y = b + a`; verify CSE eliminates the second operation.
- **CFG Branches & Preheaders:** Write `while (a < 5)` and visually confirm the injection of the preheader block and correct branch coloring in the Dagre-D3 visualization.
- **Spill Cost Simulation:** Select register limit `K=3`. Write a deeply nested `while` loop that exhausts registers. Verify via Assembly output that variables *inside* the inner loop receive registers via coalescing/coloring, while outer scope variables are systematically spilled.
