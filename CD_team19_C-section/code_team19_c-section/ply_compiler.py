import ply.lex as lex
import ply.yacc as yacc
import math

# ==========================================
# 1. LEXER
# ==========================================

keywords = {
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'for': 'FOR',
    'sin': 'SIN',
    'cos': 'COS',
    'sqrt': 'SQRT'
}

tokens = (
    'NUMBER', 'ID', 'STRING_VAL',
    'PLUS', 'MINUS', 'MULT', 'DIV', 'POW',
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
    'EQUALS', 'EQEQ', 'NEQ', 'LT', 'GT', 'LTE', 'GTE',
    'SEMI', 'COMMA'
) + tuple(keywords.values())

t_PLUS    = r'\+'
t_MINUS   = r'-'
t_MULT    = r'\*'
t_DIV     = r'/'
t_POW     = r'\^'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LBRACE  = r'\{'
t_RBRACE  = r'\}'
t_EQUALS  = r'='
t_EQEQ    = r'=='
t_NEQ     = r'!='
t_LT      = r'<'
t_GT      = r'>'
t_LTE     = r'<='
t_GTE     = r'>='
t_SEMI    = r';'
t_COMMA   = r','

t_ignore = ' \t\r'

# Keep track of line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_STRING_VAL(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = str(t.value[1:-1])
    return t

def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = keywords.get(t.value, 'ID')
    return t

def t_error(t):
    global parse_errors
    parse_errors.append({"line": t.lineno, "msg": f"Illegal character '{t.value[0]}'"})
    t.lexer.skip(1)

lexer = lex.lex()

# ==========================================
# 2. AST NODES
# ==========================================

class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, stmts):
        self.stmts = stmts
    def to_dict(self):
        return {"name": "Program", "children": [s.to_dict() for s in self.stmts if s]}

class Block(ASTNode):
    def __init__(self, stmts):
        self.stmts = stmts
    def to_dict(self):
        return {"name": "Block", "children": [s.to_dict() for s in self.stmts if s]}

class Assign(ASTNode):
    def __init__(self, id_val, expr):
        self.id_val = id_val
        self.expr = expr
    def to_dict(self):
        return {"name": "=", "children": [{"name": self.id_val}, self.expr.to_dict()]}

class BinOp(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
    def to_dict(self):
        return {"name": self.op, "children": [self.left.to_dict(), self.right.to_dict()]}

class UnaryOp(ASTNode):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr
    def to_dict(self):
        return {"name": self.op, "children": [self.expr.to_dict()]}

class FuncCall(ASTNode):
    def __init__(self, func_name, args):
        self.func_name = func_name
        self.args = args
    def to_dict(self):
        return {"name": f"Call {self.func_name}", "children": [a.to_dict() for a in self.args]}

class IfStmt(ASTNode):
    def __init__(self, cond, true_block, false_block=None):
        self.cond = cond
        self.true_block = true_block
        self.false_block = false_block
    def to_dict(self):
        children = [{"name": "Cond", "children": [self.cond.to_dict()]}, 
                    {"name": "True", "children": [self.true_block.to_dict()]}]
        if self.false_block:
            children.append({"name": "False", "children": [self.false_block.to_dict()]})
        return {"name": "If", "children": children}

class WhileStmt(ASTNode):
    def __init__(self, cond, block):
        self.cond = cond
        self.block = block
    def to_dict(self):
        return {"name": "While", "children": [{"name": "Cond", "children": [self.cond.to_dict()]}, 
                                              {"name": "Do", "children": [self.block.to_dict()]}]}

class Num(ASTNode):
    def __init__(self, val):
        self.val = val
        self.type = 'int' if isinstance(val, int) else 'float'
    def to_dict(self):
        return {"name": str(self.val)}

class StrVal(ASTNode):
    def __init__(self, val):
        self.val = val
        self.type = 'string'
    def to_dict(self):
        return {"name": f'"{self.val}"'}

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name
    def to_dict(self):
        return {"name": self.name}


# ==========================================
# 3. PARSER
# ==========================================

precedence = (
    ('left', 'EQEQ', 'NEQ', 'LT', 'GT', 'LTE', 'GTE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULT', 'DIV'),
    ('right', 'POW'),
    ('right', 'UMINUS'),
)

def p_program(p):
    '''program : statement_list'''
    p[0] = Program(p[1])

def p_statement_list(p):
    '''statement_list : statement
                      | statement_list statement'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_block(p):
    '''block : LBRACE statement_list RBRACE
             | statement'''
    if len(p) == 4:
        p[0] = Block(p[2])
    else:
        p[0] = Block([p[1]])

def p_statement_assign(p):
    '''statement : ID EQUALS expression SEMI'''
    p[0] = Assign(p[1], p[3])
    
def p_statement_expr(p):
    '''statement : expression SEMI'''
    p[0] = p[1]

def p_statement_if(p):
    '''statement : IF LPAREN expression RPAREN block
                 | IF LPAREN expression RPAREN block ELSE block'''
    if len(p) == 6:
        p[0] = IfStmt(p[3], p[5])
    else:
        p[0] = IfStmt(p[3], p[5], p[7])

def p_statement_while(p):
    '''statement : WHILE LPAREN expression RPAREN block'''
    p[0] = WhileStmt(p[3], p[5])

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression MULT expression
                  | expression DIV expression
                  | expression POW expression
                  | expression EQEQ expression
                  | expression NEQ expression
                  | expression LT expression
                  | expression GT expression
                  | expression LTE expression
                  | expression GTE expression'''
    p[0] = BinOp(p[2], p[1], p[3])

def p_expression_uminus(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = UnaryOp('-', p[2])

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_func(p):
    '''expression : SIN LPAREN expression RPAREN
                  | COS LPAREN expression RPAREN
                  | SQRT LPAREN expression RPAREN'''
    p[0] = FuncCall(p[1], [p[3]])

def p_expression_num(p):
    '''expression : NUMBER'''
    p[0] = Num(p[1])

def p_expression_str(p):
    '''expression : STRING_VAL'''
    p[0] = StrVal(p[1])

def p_expression_id(p):
    '''expression : ID'''
    p[0] = Identifier(p[1])

def p_error(p):
    global parse_errors
    if p:
        parse_errors.append({"line": p.lineno, "msg": f"Syntax error at '{p.value}'"})
        # Panic mode recovery
        parser.errok()
    else:
        parse_errors.append({"line": 0, "msg": "Syntax error at EOF"})

parser = yacc.yacc(debug=False, write_tables=False)

# ==========================================
# 3. ADVANCED OPTIMIZATIONS (CFG & LICM)
# ==========================================

def is_valid_var(v):
    """Return True only for proper identifiers (variable/temp names).
    Rejects numeric literals, string literals, operators, and keywords."""
    if not v:
        return False
    # Reject numeric literals (int or float)
    try:
        float(v)
        return False
    except ValueError:
        pass
    # Reject string literals (quoted values)
    if v.startswith('"') or v.startswith("'"):
        return False
    # Must be a valid Python identifier (covers a-z, A-Z, _, digits after first char)
    return v.isidentifier()

class BasicBlock:
    def __init__(self, bid):
        self.id = bid
        self.tac = []
        self.preds = set()
        self.succs = set()
        self.dom = set()
        self.idom = None

class ControlFlowGraph:
    def __init__(self, tac_list):
        self.tac_list = tac_list
        self.blocks = {}
        self.entry_node = "B0"
        self._build()
        if self.blocks:
            self._compute_dominators()
            self._insert_preheaders()

    def _build(self):
        leaders = {0: "B0"}
        block_counter = 1
        
        for i, line in enumerate(self.tac_list):
            if line.endswith(":"):
                leaders[i] = line[:-1]
            elif line.startswith("goto ") or line.startswith("ifFalse "):
                if i + 1 < len(self.tac_list):
                    if (i + 1) not in leaders:
                        leaders[i + 1] = f"B{block_counter}"
                        block_counter += 1
                        
        sorted_leaders = sorted(leaders.keys())
        for i, start_idx in enumerate(sorted_leaders):
            end_idx = sorted_leaders[i+1] if i + 1 < len(sorted_leaders) else len(self.tac_list)
            b_id = leaders[start_idx]
            bb = BasicBlock(b_id)
            bb.tac = self.tac_list[start_idx:end_idx]
            self.blocks[b_id] = bb
            
        if not self.blocks: return
        self.entry_node = leaders[0]

        for i, start_idx in enumerate(sorted_leaders):
            b_id = leaders[start_idx]
            bb = self.blocks[b_id]
            last_line = bb.tac[-1] if bb.tac else ""
            
            if last_line.startswith("goto "):
                target = last_line.split(" ")[1]
                if target in self.blocks:
                    bb.succs.add(target)
                    self.blocks[target].preds.add(b_id)
            elif last_line.startswith("ifFalse "):
                target = last_line.split(" ")[-1]
                if target in self.blocks:
                    bb.succs.add(target)
                    self.blocks[target].preds.add(b_id)
                if i + 1 < len(sorted_leaders):
                    next_id = leaders[sorted_leaders[i+1]]
                    bb.succs.add(next_id)
                    self.blocks[next_id].preds.add(b_id)
            else:
                if i + 1 < len(sorted_leaders):
                    next_id = leaders[sorted_leaders[i+1]]
                    bb.succs.add(next_id)
                    self.blocks[next_id].preds.add(b_id)

    def _compute_dominators(self):
        nodes = list(self.blocks.keys())
        for n in nodes: self.blocks[n].dom = set(nodes)
        if self.entry_node in self.blocks:
            self.blocks[self.entry_node].dom = {self.entry_node}

        changed = True
        while changed:
            changed = False
            for n in nodes:
                if n == self.entry_node: continue
                preds = self.blocks[n].preds
                if not preds: new_dom = {n}
                else:
                    intersect = set(nodes)
                    for p in preds: intersect = intersect.intersection(self.blocks[p].dom)
                    new_dom = {n}.union(intersect)
                if new_dom != self.blocks[n].dom:
                    self.blocks[n].dom = new_dom
                    changed = True

        # Compute immediate dominators using proper algorithm
        # idom(n) = unique strict dominator of n that doesn't dominate any other strict dominator
        for n in nodes:
            if n == self.entry_node:
                self.blocks[n].idom = None
                continue
            doms_of_n = self.blocks[n].dom - {n}
            if not doms_of_n:
                self.blocks[n].idom = None
                continue
            # idom is the strict dominator with no other strict dominator between it and n
            idom_candidate = None
            for d in doms_of_n:
                is_idom = True
                for other in doms_of_n:
                    if other != d and d in self.blocks[other].dom:
                        is_idom = False
                        break
                if is_idom:
                    idom_candidate = d
                    break
            self.blocks[n].idom = idom_candidate

    def _insert_preheaders(self):
        loops = []
        for n in self.blocks:
            for succ in self.blocks[n].succs:
                if succ in self.blocks[n].dom:
                    loops.append((succ, n))
                    
        headers = set([h for h, t in loops])
        preheader_count = 0
        
        for header in headers:
            preheader_count += 1
            ph_id = f"PH_{header}_{preheader_count}"
            ph = BasicBlock(ph_id)
            ph.tac = [f"{ph_id}:", f"goto {header}"]
            
            entering_preds = []
            for p in self.blocks[header].preds:
                if header not in self.blocks[p].dom:
                    entering_preds.append(p)
                    
            if not entering_preds: continue
            self.blocks[ph_id] = ph
            
            for p in entering_preds:
                self.blocks[p].succs.remove(header)
                self.blocks[p].succs.add(ph_id)
                self.blocks[header].preds.remove(p)
                ph.preds.add(p)
                
                pb = self.blocks[p]
                if pb.tac:
                    last_line = pb.tac[-1]
                    if last_line.startswith("goto " + header):
                        pb.tac[-1] = f"goto {ph_id}"
                    elif last_line.startswith("ifFalse ") and last_line.split(" ")[-1] == header:
                        parts = last_line.split(" ")
                        parts[-1] = ph_id
                        pb.tac[-1] = " ".join(parts)
            
            ph.succs.add(header)
            self.blocks[header].preds.add(ph_id)

    def build_line_map(self):
        """Correct mapping using stable indices (no string matching)."""
        self.line_map = {}
        self.block_lines = {}

        idx = 0
        for b_id, bb in self.blocks.items():
            self.block_lines[b_id] = []
            for _ in bb.tac:
                self.line_map[idx] = b_id
                self.block_lines[b_id].append(idx)
                idx += 1

    def flatten(self):
        visited = set()
        flattened = []
        def visit(node_id):
            if node_id in visited: return
            visited.add(node_id)
            bb = self.blocks[node_id]
            if bb.tac and not bb.tac[0].endswith(":"):
                if node_id.startswith("B") or node_id.startswith("PH_"): pass
            flattened.extend(bb.tac)

            explicit_targets = set()
            if bb.tac:
                last_line = bb.tac[-1]
                if last_line.startswith("goto "): explicit_targets.add(last_line.split(" ")[1])
                elif last_line.startswith("ifFalse "): explicit_targets.add(last_line.split(" ")[-1])

            fallthrough = None
            for succ in bb.succs:
                if succ not in explicit_targets:
                    fallthrough = succ
                    break

            if fallthrough:
                if fallthrough in visited:
                    flattened.append(f"goto {fallthrough}")
                else:
                    visit(fallthrough)
        visit(self.entry_node)
        return flattened

    def compute_liveness(self):
        # BUG FIX: Never call flatten() inside analysis! It reorders instructions 
        # and makes index-based maps (inst_out) invalid.
        tac = self.tac_list
        
        succs = {i: set() for i in range(len(tac))}
        labels = {}
        for i, line in enumerate(tac):
            if line.endswith(":"):
                labels[line[:-1]] = i
                
        for i, line in enumerate(tac):
            if line.startswith("goto "):
                target = line.split(" ")[1]
                if target in labels: succs[i].add(labels[target])
            elif line.startswith("ifFalse "):
                target = line.split(" ")[-1]
                if target in labels: succs[i].add(labels[target])
                if i + 1 < len(tac): succs[i].add(i + 1)
            elif line.startswith("return "):
                pass
            else:
                if i + 1 < len(tac): succs[i].add(i + 1)
                
        USE = {}
        DEF = {}
        for i, line in enumerate(tac):
            u, d = set(), set()
            parts = line.split(" ")
            if len(parts) >= 3 and parts[1] == '=':
                if is_valid_var(parts[0]):
                    d.add(parts[0])
                for j in range(2, len(parts)):
                    try: float(parts[j])
                    except ValueError:
                        val = parts[j].replace(',', '')
                        if val not in ('call', 'sin', 'cos', 'sqrt', '+', '-', '*', '/', '^', '==', '!=', '<', '>', '<=', '>=') and is_valid_var(val):
                            u.add(val)
            elif line.startswith("ifFalse "):
                try: float(parts[1])
                except ValueError:
                    if is_valid_var(parts[1]):
                        u.add(parts[1])
            elif line.startswith("return "):
                try: float(parts[1])
                except ValueError:
                    if is_valid_var(parts[1]):
                        u.add(parts[1])
            USE[i] = u
            DEF[i] = d

        IN = {i: set() for i in range(len(tac))}
        OUT = {i: set() for i in range(len(tac))}
        
        changed = True
        while changed:
            changed = False
            for i in range(len(tac)-1, -1, -1):
                old_in = IN[i].copy()
                old_out = OUT[i].copy()
                
                new_out = set()
                for s in succs[i]:
                    new_out.update(IN[s])
                    
                OUT[i] = new_out
                
                IN[i] = USE[i].union(OUT[i].difference(DEF[i]))
                if IN[i] != old_in or OUT[i] != old_out:
                    changed = True
                    
        self.inst_in = IN
        self.inst_out = OUT
        self.inst_use = USE
        self.inst_def = DEF

class LICMOptimizer:
    def __init__(self, cfg):
        self.cfg = cfg
        self.changed = False
        self.hoist_count = 1
        
    def get_loop_blocks(self, header, tails):
        loop_blocks = {header}
        stack = list(tails)
        for t in tails: loop_blocks.add(t)
        
        while stack:
            n = stack.pop()
            for p in self.cfg.blocks[n].preds:
                if p not in loop_blocks:
                    loop_blocks.add(p)
                    stack.append(p)
        return loop_blocks
        
    def optimize(self):
        loops = {}
        for n in self.cfg.blocks:
            for succ in self.cfg.blocks[n].succs:
                if succ in self.cfg.blocks[n].dom:
                    if succ not in loops: loops[succ] = set()
                    loops[succ].add(n)
                    
        for header, tails in loops.items():
            loop_blocks = self.get_loop_blocks(header, tails)
            
            assigned_in_loop = set()
            for b_id in loop_blocks:
                for line in self.cfg.blocks[b_id].tac:
                    parts = line.split(" ")
                    if len(parts) >= 3 and parts[1] == '=':
                        assigned_in_loop.add(parts[0])
                        
            ph_id = None
            for p in self.cfg.blocks[header].preds:
                if p not in loop_blocks:
                    ph_id = p
                    break
                    
            if not ph_id: continue
            ph = self.cfg.blocks[ph_id]
            
            for b_id in loop_blocks:
                bb = self.cfg.blocks[b_id]
                new_tac = []
                for line in bb.tac:
                    parts = line.split(" ")
                    if len(parts) >= 3 and parts[1] == '=':
                        dest = parts[0]
                        invariant = True
                        
                        # Validate purity
                        has_call = False
                        for p in parts:
                            if p == 'call': has_call = True
                        
                        if has_call:
                            # Only pure math functions are hoisted!
                            func_name = parts[3].replace(',', '')
                            if func_name not in ['sin', 'cos', 'sqrt']:
                                invariant = False
                                
                        # Check dependencies
                        for idx in range(2, len(parts)):
                            val = parts[idx].replace(',', '')
                            if val in ['call', '+', '-', '*', '/', '^', '<', '>', '<=', '>=', '==', '!=']: continue
                            if val in ['sin', 'cos', 'sqrt']: continue
                            if val in assigned_in_loop:
                                invariant = False
                                break
                        
                        if invariant:
                            if not dest.startswith("t_hoist_"):
                                t_hoist = f"t_hoist_{self.hoist_count}"
                                self.hoist_count += 1
                                hoist_line = line.replace(dest, t_hoist, 1)
                                
                                insert_idx = len(ph.tac)
                                if ph.tac and (ph.tac[-1].startswith("goto") or ph.tac[-1].startswith("ifFalse")):
                                    insert_idx -= 1
                                ph.tac.insert(insert_idx, hoist_line)
                                
                                new_tac.append(f"{dest} = {t_hoist}")
                                self.changed = True
                                continue
                            
                    new_tac.append(line)
                bb.tac = new_tac

class GraphColoringAllocator:
    def __init__(self, tac_list, k=4):
        self.tac_list = tac_list
        self.interference = {}
        self.reg_map = {}
        self.spilled = set()
        self.k = k

        # Exclude loop iterators entirely from Graph Coloring Register Allocation
        self.exclude_vars = set()
        for line in tac_list:
            if " = " in line and " + 1" in line:
                dest = line.split(" ")[0]
                if len(dest) == 1:
                    self.exclude_vars.add(dest)

        self.ops = {'+', '-', '*', '/', '^', '==', '!=', '<', '>', '<=', '>='}
        
    def allocate(self):
        cfg = ControlFlowGraph(self.tac_list)
        cfg.compute_liveness()
        self.tac_list = cfg.tac_list
        USE = cfg.inst_use
        DEF = cfg.inst_def
        OUT = cfg.inst_out

        for u_set in USE.values():
            for v in u_set:
                if is_valid_var(v):
                    self.interference.setdefault(v, set())
        for d_set in DEF.values():
            for v in d_set:
                if is_valid_var(v):
                    self.interference.setdefault(v, set())
            
        for i in range(len(self.tac_list)):
            for d in DEF.get(i, set()):
                if not is_valid_var(d):
                    continue
                for l in OUT[i]:
                    if d != l and is_valid_var(l):
                        self.interference[d].add(l)
                        self.interference.setdefault(l, set()).add(d)

        uncolored = list(self.interference.keys())
        stack = []
        
        is_temp = lambda v: v.startswith('t') and (v[1:].isdigit() or v.startswith('t_hoist_'))
        get_k = lambda v: 7 if is_temp(v) else self.k
        
        def current_degree(n):
            """Number of neighbors still in the uncolored set."""
            return len([x for x in self.interference[n] if x in uncolored])
        
        # --- Phase 1: Simplify (push to stack) ---
        while uncolored:
            candidates = [n for n in uncolored if current_degree(n) < get_k(n)]
            if candidates:
                # Pick highest-degree candidate first for better distribution
                candidates.sort(key=lambda n: current_degree(n), reverse=True)
                node = candidates[0]
                uncolored.remove(node)
                stack.append(node)
            else:
                # Spill heuristic: prefer spilling temps over user vars;
                # among equals, spill the highest-degree node
                def spill_priority(n):
                    return (not is_temp(n), current_degree(n))
                spill_candidate = max(uncolored, key=spill_priority)
                uncolored.remove(spill_candidate)
                stack.append(spill_candidate)

        available_colors_s = [f"$s{i}" for i in range(self.k)]
        available_colors_t = [f"$t{i}" for i in range(7)]
        
        # Track next rotation index per pool to avoid $s0/$t0 clustering
        self._next_s = 0
        self._next_t = 0
        
        # --- Phase 2: Select (assign registers) ---
        while stack:
            n = stack.pop()
            neighbor_colors = {self.reg_map[neighbor] for neighbor in self.interference[n] if neighbor in self.reg_map}
            color = None
            pool = available_colors_t if is_temp(n) else available_colors_s
            pool_size = len(pool)
            
            # Determine rotation start index for this pool
            start = self._next_t if is_temp(n) else self._next_s
            
            # Cyclic rotation: walk the pool starting from the rotation index
            # to distribute variables evenly across available registers
            for offset in range(pool_size):
                c = pool[(start + offset) % pool_size]
                if c not in neighbor_colors:
                    color = c
                    # Advance rotation so next variable starts at the next slot
                    if is_temp(n):
                        self._next_t = (start + offset + 1) % pool_size
                    else:
                        self._next_s = (start + offset + 1) % pool_size
                    break
            
            if color:
                self.reg_map[n] = color
            else:
                self.spilled.add(n)
                
        self.out_sets = OUT
        return self.reg_map

# ==========================================
# 4. COMPILER ENGINE (Semantics, TAC, Opt, Asm)
# ==========================================

def ast_to_string(node):
    if node is None:
        return ""
    if isinstance(node, Num):
        return str(node.val)
    elif isinstance(node, StrVal):
        return f'"{node.val}"'
    elif isinstance(node, Identifier):
        return node.name
    elif isinstance(node, FuncCall):
        args_str = ", ".join(ast_to_string(a) for a in node.args)
        return f"{node.func_name}({args_str})"
    elif isinstance(node, BinOp):
        return f"({ast_to_string(node.left)} {node.op} {ast_to_string(node.right)})"
    elif isinstance(node, UnaryOp):
        return f"({node.op}{ast_to_string(node.expr)})"
    return "unknown"

class CompilerEngine:
    def __init__(self):
        self.tac = []
        self.temp_count = 0
        self.label_count = 0
        self.symbol_table = {}
        self.semantic_errors = []

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, instruction):
        self.tac.append(instruction)

    def infer_type(self, node):
        if isinstance(node, Num):
            return node.type
        elif isinstance(node, StrVal):
            return "string"
        elif isinstance(node, FuncCall):
            return "float"
        elif isinstance(node, Identifier):
            if node.name in self.symbol_table:
                return self.symbol_table[node.name]["type"]
            return "unknown"
        elif isinstance(node, BinOp):
            l_type = self.infer_type(node.left)
            r_type = self.infer_type(node.right)
            if l_type == "float" or r_type == "float":
                return "float"
            if l_type == "int" and r_type == "int":
                return "int"
            return "unknown"
        return "unknown"

    def analyze_and_gen(self, node):
        if node is None:
            return None

        if isinstance(node, Program) or isinstance(node, Block):
            for stmt in node.stmts:
                self.analyze_and_gen(stmt)
            return None

        elif isinstance(node, Num):
            return node.val

        elif isinstance(node, StrVal):
            return f'"{node.val}"'

        elif isinstance(node, Identifier):
            if node.name not in self.symbol_table:
                self.semantic_errors.append(f"Undefined variable: '{node.name}'")
                return node.name # Proceed anyway to avoid cascade
            return node.name

        elif isinstance(node, Assign):
            val = self.analyze_and_gen(node.expr)
            raw_str = ast_to_string(node.expr)
            # Update symbol table utilizing recursive type promotion inference
            t = self.infer_type(node.expr)
            self.symbol_table[node.id_val] = {"type": t, "expr": raw_str, "value": "unknown"}
            self.emit(f"{node.id_val} = {val}")
            return node.id_val

        elif isinstance(node, BinOp):
            l = self.analyze_and_gen(node.left)
            r = self.analyze_and_gen(node.right)
            
            # Simple Semantic Check: Don't string-math if not PLUS
            if isinstance(node.left, StrVal) or isinstance(node.right, StrVal):
                if node.op != '+':
                    self.semantic_errors.append(f"Type Mismatch: Cannot use '{node.op}' on strings.")

            t = self.new_temp()
            self.emit(f"{t} = {l} {node.op} {r}")
            return t

        elif isinstance(node, UnaryOp):
            val = self.analyze_and_gen(node.expr)
            t = self.new_temp()
            self.emit(f"{t} = {node.op} {val}")
            return t

        elif isinstance(node, FuncCall):
            a = self.analyze_and_gen(node.args[0])
            t = self.new_temp()
            self.emit(f"{t} = call {node.func_name}, {a}")
            return t

        elif isinstance(node, IfStmt):
            cond = self.analyze_and_gen(node.cond)
            l_true = self.new_label()
            l_end = self.new_label()
            
            if node.false_block:
                l_false = self.new_label()
                self.emit(f"ifFalse {cond} goto {l_false}")
                self.analyze_and_gen(node.true_block)
                self.emit(f"goto {l_end}")
                self.emit(f"{l_false}:")
                self.analyze_and_gen(node.false_block)
                self.emit(f"{l_end}:")
            else:
                self.emit(f"ifFalse {cond} goto {l_end}")
                self.analyze_and_gen(node.true_block)
                self.emit(f"{l_end}:")
            return None

        elif isinstance(node, WhileStmt):
            l_start = self.new_label()
            l_end = self.new_label()
            self.emit(f"{l_start}:")
            cond = self.analyze_and_gen(node.cond)
            self.emit(f"ifFalse {cond} goto {l_end}")
            self.analyze_and_gen(node.block)
            self.emit(f"goto {l_start}")
            self.emit(f"{l_end}:")
            return None

        return None

    def _pass_remove_useless_jumps(self, tac):
        clean_tac = []
        changed = False
        for i, line in enumerate(tac):
            if line.startswith("goto "):
                target = line.split(" ")[1] + ":"
                # Remove goto if next line IS the target (fallthrough)
                if i + 1 < len(tac) and tac[i+1] == target:
                    changed = True
                    continue
                # Remove goto at the very end of TAC (dangling jump)
                if i == len(tac) - 1:
                    changed = True
                    continue
            clean_tac.append(line)
        return changed, clean_tac

    def _pass_temporary_inlining(self, tac):
        inline_tac = []
        changed = False
        i = 0
        while i < len(tac):
            line = tac[i]
            if i + 1 < len(tac):
                next_line = tac[i+1]
                parts1 = line.split(" ")
                parts2 = next_line.split(" ")
                if len(parts1) >= 3 and parts1[1] == '=' and len(parts2) == 3 and parts2[1] == '=':
                    dest1 = parts1[0]
                    is_temp1 = (len(dest1) > 1 and dest1[0] == 't' and dest1[1:].isdigit()) or dest1.startswith("t_hoist_")
                    if is_temp1:
                        dest2 = parts2[0]
                        src2 = parts2[2]
                        if src2 == dest1:
                            new_line = dest2 + " = " + " ".join(parts1[2:])
                            inline_tac.append(new_line)
                            changed = True
                            i += 2
                            continue
            inline_tac.append(line)
            i += 1
        return changed, inline_tac

    def _pass_unreachable_code(self, tac):
        changed = False
        active_labels = set()
        for line in tac:
            if line.startswith("goto "): active_labels.add(line.split(" ")[1])
            elif line.startswith("ifFalse "): active_labels.add(line.split(" ")[3])

        reachable_tac = []
        reachable = True
        for line in tac:
            if line.endswith(":"):
                label_name = line[:-1]
                if not reachable and label_name not in active_labels:
                    changed = True
                    continue
                reachable = True
            
            if not reachable:
                changed = True
                continue
                
            reachable_tac.append(line)
            if line.startswith("goto "):
                reachable = False
                
        return changed, reachable_tac

    def _pass_dead_store_elimination(self, tac, inst_out):
        """Remove assignments to temporaries whose LHS is not live afterward.
        Preserved user variables while optimizing away dead intermediate temporaries.
        """
        changed = False
        final_tac = []
        
        # --- Correctness Fix: Protect all variables used in control flow or as arguments ---
        # Even if liveness analysis (due to index shifts or edge cases) thinks they are dead,
        # if they are used as a source in critical ops, we MUST preserve their definition.
        protected_vars = set()
        for line in tac:
            parts = line.split()
            if not parts: continue
            # 1. Branch/Return conditions
            if parts[0] in ("ifFalse", "if") and len(parts) > 1:
                protected_vars.add(parts[1])
            elif parts[0] == "return" and len(parts) > 1:
                if is_valid_var(parts[1]): protected_vars.add(parts[1])
            # 2. Call arguments: t = call f, arg
            elif 'call' in parts and len(parts) >= 5:
                arg = parts[4].replace(',', '')
                if is_valid_var(arg): protected_vars.add(arg)

        # --- Safety Shield: Helper to scan for downstream uses ---
        def has_downstream_use(var, start_idx):
            for j in range(start_idx + 1, len(tac)):
                l = tac[j]
                if l.endswith(":"): continue
                lp = l.split()
                if var in lp[1:]: return True
                if len(lp) >= 2 and lp[1] == '=' and lp[0] == var: return False
            return False

        for i, line in enumerate(tac):
            if line.endswith(":"):
                final_tac.append(line)
                continue
                
            parts = line.split(" ")
            if len(parts) >= 3 and parts[1] == '=':
                dest = parts[0]
                is_call = 'call' in parts
                if is_valid_var(dest):
                    # Protection 1: Never remove variables used in upcoming control flow or calls
                    if dest in protected_vars:
                        final_tac.append(line)
                        continue
                        
                    # Protection 2: Standard liveness-based elimination for temporaries
                    is_temp = len(dest) > 1 and dest[0] == 't' and (dest[1:].isdigit() or dest.startswith("t_hoist_"))
                    if is_temp and not is_call:
                        # Check OUT set
                        is_live = dest in inst_out.get(i, set())
                        # If not live in OUT, do the Safety Shield Scan
                        if not is_live:
                            if has_downstream_use(dest, i):
                                final_tac.append(line)
                                continue
                            else:
                                changed = True
                                continue
            final_tac.append(line)

        return changed, final_tac

    def _validate_tac_integrity(self, tac):
        """Non-crashing validation to catch 'use-before-def' bugs in the optimizer."""
        defined = set()
        warnings = []
        for i, line in enumerate(tac):
            if line.endswith(":"): continue
            parts = line.split()
            if not parts: continue
            
            # 1. Identify uses (skip LHS of assignment)
            start_idx = 2 if (len(parts) >= 2 and parts[1] == '=') else 0
            for j in range(start_idx, len(parts)):
                p = parts[j].replace(',', '')
                if is_valid_var(p) and p not in defined:
                    # Ignore constants and reserved words
                    if not (p.replace('-','').isdigit() or p in ('call', 'goto', 'ifFalse', 'if', 'return')):
                        warnings.append(f"Line {i}: Variable '{p}' used without prior definition in TAC: '{line}'")
            
            # 2. Record definitions
            if len(parts) >= 2 and parts[1] == '=':
                defined.add(parts[0])
        
        if warnings:
            print("\n[TAC OPTIMIZER WARNINGS]")
            for w in warnings[:10]: # Don't flood the console
                print(f"  ! {w}")
            if len(warnings) > 10: print(f"  ... and {len(warnings)-10} more")
        return warnings
        
    def _pass_strength_reduction(self, tac):
        changed = False
        new_tac = []
        
        def _is_numeric(s):
            try: float(s); return True
            except ValueError: return False
        
        def _num_eq(s, val):
            """Check if string s represents the numeric value val."""
            try: return float(s) == val
            except ValueError: return False
        
        for line in tac:
            parts = line.split(" ")
            if len(parts) == 5 and parts[1] == '=':
                dest, op, left, right = parts[0], parts[3], parts[2], parts[4]
                # x * 2 -> x + x  (only when x is not a literal)
                if op == '*' and _num_eq(right, 2) and not _is_numeric(left):
                    new_tac.append(f"{dest} = {left} + {left}")
                    changed = True; continue
                elif op == '*' and _num_eq(left, 2) and not _is_numeric(right):
                    new_tac.append(f"{dest} = {right} + {right}")
                    changed = True; continue
                # x ^ 2 -> x * x
                elif op == '^' and _num_eq(right, 2):
                    new_tac.append(f"{dest} = {left} * {left}")
                    changed = True; continue
                # x / 1 -> x
                elif op == '/' and _num_eq(right, 1):
                    new_tac.append(f"{dest} = {left}")
                    changed = True; continue
            new_tac.append(line)
        return changed, new_tac

    def _pass_unused_labels(self, tac):
        active_labels = set()
        for line in tac:
            if line.startswith("goto "): active_labels.add(line.split(" ")[1])
            elif line.startswith("ifFalse "): active_labels.add(line.split(" ")[3])

        clean_tac = []
        changed = False
        for line in tac:
            if line.endswith(":"):
                label_name = line[:-1]
                if label_name not in active_labels:
                    changed = True
                    continue
            clean_tac.append(line)
        return changed, clean_tac



    def _pass_constant_propagation(self, tac, cfg):
        """Dataflow-based constant propagation. Only replaces variables with known constants.
        Does NOT fold expressions — that belongs in _pass_constant_folding."""
        changed_overall = False
        IN_const = {b_id: {} for b_id in cfg.blocks}
        OUT_const = {b_id: {} for b_id in cfg.blocks}

        # TOP: variable may be constant
        # BOT: conflicting values, kill the constant
        # We use {} as TOP (no info), specific value as const, key deleted as BOT

        df_changed = True
        while df_changed:
            df_changed = False
            for b_id, bb in cfg.blocks.items():
                old_out = OUT_const[b_id].copy()

                if bb.preds:
                    first_pred = True
                    for p in bb.preds:
                        if first_pred:
                            IN_const[b_id] = OUT_const[p].copy()
                            first_pred = False
                        else:
                            keys = list(IN_const[b_id].keys())
                            for k in keys:
                                if k not in OUT_const[p] or OUT_const[p][k] != IN_const[b_id][k]:
                                    del IN_const[b_id][k]  # BOT - conflicting constants

                curr_consts = IN_const[b_id].copy()
                aliases = {}

                new_tac = []
                block_changed = False

                for line in bb.tac:
                    parts = line.split(" ")
                    if line.endswith(":"):
                        new_tac.append(line)
                        continue

                    start_idx = 2 if (len(parts) >= 2 and parts[1] == '=') else 0
                    for i in range(start_idx, len(parts)):
                        if parts[i] in curr_consts:
                            parts[i] = str(curr_consts[parts[i]])
                            block_changed = True
                        elif parts[i] in aliases:
                            parts[i] = str(aliases[parts[i]])
                            block_changed = True

                    line_rebuilt = " ".join(parts)
                    assigned_var = parts[0] if (len(parts) > 1 and parts[1] == '=') else None

                    if assigned_var:
                        aliases = {k: v for k, v in aliases.items() if v != assigned_var}
                        if assigned_var in curr_consts:
                            del curr_consts[assigned_var]

                    # Pure propagation: simple copy or alias only
                    if len(parts) == 3 and parts[1] == '=':
                        try:
                            val = float(parts[2])
                            if val.is_integer(): val = int(val)
                            curr_consts[parts[0]] = val
                        except ValueError:
                            # Only alias to non-temporary variables
                            # (temporaries can be eliminated by DSE, creating dangling refs)
                            src = parts[2]
                            is_temp_src = (len(src) > 1 and src[0] == 't' and src[1:].isdigit()) or src.startswith("t_hoist_")
                            if not is_temp_src:
                                aliases[parts[0]] = src

                    # NO folding of binary expressions here.
                    # Only propagate through simple copies.

                    new_tac.append(line_rebuilt)

                OUT_const[b_id] = curr_consts
                if OUT_const[b_id] != old_out:
                    df_changed = True

                if block_changed:
                    bb.tac = new_tac
                    changed_overall = True

        # Reconstruct TAC from blocks preserving original order (not DFS)
        result_tac = []
        for b_id in cfg.blocks:
            result_tac.extend(cfg.blocks[b_id].tac)
        return changed_overall, result_tac

    def _pass_constant_folding(self, tac):
        changed = False
        new_tac = []
        for line in tac:
            parts = line.split(" ")
            if len(parts) == 5 and parts[1] == '=':
                try: left = float(parts[2]); is_left_const = True
                except ValueError: is_left_const = False
                try: right = float(parts[4]); is_right_const = True
                except ValueError: is_right_const = False
                op = parts[3]
                
                if is_left_const and is_right_const:
                    left_val = float(parts[2])
                    right_val = float(parts[4])
                    res = None
                    if op == '/':
                        if right_val == 0:
                            if not hasattr(self, 'semantic_errors'): self.semantic_errors = []
                            msg = "Division by zero detected at compile time"
                            if msg not in self.semantic_errors:
                                self.semantic_errors.append(msg)
                        else:
                            res = left_val / right_val
                    else:
                        if op == '+': res = left_val + right_val
                        elif op == '-': res = left_val - right_val
                        elif op == '*': res = left_val * right_val
                        elif op == '==': res = 1 if left_val == right_val else 0
                        elif op == '!=': res = 1 if left_val != right_val else 0
                        elif op == '<':  res = 1 if left_val < right_val else 0
                        elif op == '>':  res = 1 if left_val > right_val else 0
                        elif op == '<=': res = 1 if left_val <= right_val else 0
                        elif op == '>=': res = 1 if left_val >= right_val else 0
                    
                    if res is not None:
                        if isinstance(res, float) and res.is_integer(): res = int(res)
                        new_tac.append(f"{parts[0]} = {res}")
                        changed = True
                        continue
            elif len(parts) == 4 and parts[0] == 'ifFalse':
                try:
                    c_val = float(parts[1])
                    if c_val == 0:
                        new_tac.append(f"goto {parts[3]}")
                        changed = True; continue
                    else:
                        changed = True; continue 
                except ValueError:
                    pass
                    
            new_tac.append(line)
        return changed, new_tac

    def _pass_global_cse(self, tac, cfg):
        changed_overall = False
        dom_tree = {n: [] for n in cfg.blocks}
        for n in cfg.blocks:
            idom = None
            for d in cfg.blocks[n].dom:
                if d != n:
                    is_idom = True
                    for other in cfg.blocks[n].dom:
                        if other != n and other != d and d in cfg.blocks[other].dom:
                            is_idom = False
                            break
                    if is_idom: idom = d
            if idom:
                dom_tree[idom].append(n)
                
        def traverse(n, avail_exprs):
            nonlocal changed_overall
            bb = cfg.blocks[n]
            new_tac = []
            block_changed = False
            
            curr_exprs = avail_exprs.copy()
            
            for line in bb.tac:
                parts = line.split(" ")
                
                if line.endswith(":") or line.startswith("goto") or line.startswith("ifFalse"):
                    new_tac.append(line)
                    continue
                    
                if len(parts) == 5 and parts[1] == '=':
                    dest, left, op, right = parts[0], parts[2], parts[3], parts[4]
                    if op in ('+', '*', '==', '!='):
                        c_left, c_right = min(left, right), max(left, right)
                    else:
                        c_left, c_right = left, right
                        
                    expr_key = f"{c_left} {op} {c_right}"
                    
                    if expr_key in curr_exprs:
                        new_line = f"{dest} = {curr_exprs[expr_key]}"
                        new_tac.append(new_line)
                        block_changed = True
                    else:
                        curr_exprs[expr_key] = dest
                        new_tac.append(line)
                        
                    is_temp = len(dest) > 1 and dest[0] == 't' and dest[1:].isdigit()
                    if not is_temp:
                        to_remove = [k for k in curr_exprs if dest in k.split(" ")]
                        for k in to_remove:
                            del curr_exprs[k]
                        to_remove_val = [k for k, v in curr_exprs.items() if v == dest and k != expr_key]
                        for k in to_remove_val:
                            del curr_exprs[k]

                elif len(parts) >= 3 and parts[1] == '=':
                    dest = parts[0]
                    new_tac.append(line)
                    
                    is_temp = len(dest) > 1 and dest[0] == 't' and dest[1:].isdigit()
                    if not is_temp:
                        to_remove = [k for k in curr_exprs if dest in k.split(" ")]
                        for k in to_remove:
                            del curr_exprs[k]
                        to_remove_val = [k for k, v in curr_exprs.items() if v == dest]
                        for k in to_remove_val:
                            del curr_exprs[k]
                else:
                    new_tac.append(line)
                    
            if block_changed:
                bb.tac = new_tac
                changed_overall = True
                
            for child in dom_tree[n]:
                traverse(child, curr_exprs)
                
        traverse(cfg.entry_node, {})
        # Reconstruct TAC from blocks preserving original order (not DFS)
        result_tac = []
        for b_id in cfg.blocks:
            result_tac.extend(cfg.blocks[b_id].tac)
        return changed_overall, result_tac

    def optimize_tac(self):
        opt_tac = self.tac[:]
        changed = True
        iteration = 0
        MAX_ITER = 50

        while changed and iteration < MAX_ITER:
            iteration += 1
            changed = False

            cfg = ControlFlowGraph(opt_tac)
            cfg.compute_liveness()
            cfg.build_line_map()

            # --- CSE first (before propagation) so symbolic reuse is preserved ---
            c, opt_tac = self._pass_global_cse(opt_tac, cfg)
            changed = changed or c

            # --- Constant Propagation ---
            if changed:
                cfg = ControlFlowGraph(opt_tac)
                cfg.compute_liveness()
                cfg.build_line_map()
            c, opt_tac = self._pass_constant_propagation(opt_tac, cfg)
            changed = changed or c

            # --- Constant Folding ---
            c, opt_tac = self._pass_constant_folding(opt_tac)
            changed = changed or c

            # --- Strength Reduction ---
            c, opt_tac = self._pass_strength_reduction(opt_tac)
            changed = changed or c

            # --- Unreachable Code (in main loop so dead branches are cleaned
            #     before next propagation round — enables q/r/s/t folding) ---
            c, opt_tac = self._pass_unreachable_code(opt_tac)
            changed = changed or c

            # --- Dead Store Elimination (temporaries only) ---
            if changed:
                cfg = ControlFlowGraph(opt_tac)
                cfg.compute_liveness()
                cfg.build_line_map()
            c, opt_tac = self._pass_dead_store_elimination(opt_tac, cfg.inst_out)
            changed = changed or c

            # --- LICM ---
            cfg = ControlFlowGraph(opt_tac)
            cfg.build_line_map()
            licm = LICMOptimizer(cfg)
            c_licm = licm.optimize()
            if c_licm:
                opt_tac = cfg.flatten()
                changed = True

        # === Cleanup Phase ===
        cleanup_changed = True
        cleanup_iteration = 0
        while cleanup_changed and cleanup_iteration < MAX_ITER:
            cleanup_iteration += 1
            cleanup_changed = False
            c, opt_tac = self._pass_remove_useless_jumps(opt_tac)
            cleanup_changed = cleanup_changed or c

            c, opt_tac = self._pass_temporary_inlining(opt_tac)
            cleanup_changed = cleanup_changed or c

            c, opt_tac = self._pass_unreachable_code(opt_tac)
            if c:
                cleanup_changed = True
                continue

            c, opt_tac = self._pass_unused_labels(opt_tac)
            cleanup_changed = cleanup_changed or c

        # Final Integrity Check
        self._validate_tac_integrity(opt_tac)
        return opt_tac

    def _peephole_optimize_asm(self, asm):
        """Pass over generated assembly to remove redundant/dead instructions."""
        optimized_asm = []
        i = 0
        while i < len(asm):
            line = asm[i]
            stripped = line.strip()
            indent = line[:len(line) - len(stripped)]
            
            # 1. Remove redundant MOVE $rx, $rx
            if stripped.startswith("MOVE "):
                parts = stripped.replace(',', '').split()
                if len(parts) == 3 and parts[1] == parts[2]:
                    i += 1
                    continue
            
            # 2. Collapse LI overwrite chains: LI $r0, 10 \n LI $r0, 20 -> LI $r0, 20
            if stripped.startswith("LI ") and i + 1 < len(asm):
                next_stripped = asm[i+1].strip()
                if next_stripped.startswith("LI "):
                    p1 = stripped.replace(',', '').split()
                    p2 = next_stripped.replace(',', '').split()
                    if p1[1] == p2[1]: # Same register overwritten immediately
                        i += 1
                        continue

            # 3. Remove redundant LOAD-MOVE: LI $t0, 5 \n MOVE $t1, $t0 -> LI $t1, 5
            if stripped.startswith("LI ") and i + 1 < len(asm):
                next_stripped = asm[i+1].strip()
                if next_stripped.startswith("MOVE "):
                    p1 = stripped.replace(',', '').split()
                    p2 = next_stripped.replace(',', '').split()
                    if p1[1] == p2[2]:
                        optimized_asm.append(f"{indent}LI {p2[1]}, {p1[2]}")
                        i += 2
                        continue

            # 4. Remove redundant SW+LW (store then immediate reload from same slot)
            if stripped.startswith("SW ") and i + 1 < len(asm):
                next_stripped = asm[i+1].strip()
                if next_stripped.startswith("LW "):
                    p_sw = stripped.replace(',', '').split()
                    p_lw = next_stripped.replace(',', '').split()
                    if len(p_sw) == 3 and len(p_lw) == 3 and p_sw[1] == p_lw[1] and p_sw[2] == p_lw[2]:
                        i += 2
                        continue
                        
            # 5. Remove J to next label (unconditional jump to immediate successor)
            if stripped.startswith("J ") and not stripped.startswith("JAL") and i + 1 < len(asm):
                target = stripped.split(" ")[-1]
                if asm[i+1].strip() == f"{target}:":
                    i += 1
                    continue

            optimized_asm.append(line)
            i += 1
            
        return optimized_asm

    def generate_assembly(self, optimized_tac, k_regs=4):
        """Generates correct, efficient MIPS assembly using graph-coloring results."""
        allocator = GraphColoringAllocator(optimized_tac, k=k_regs)
        reg_map = allocator.allocate()
        
        # Scratch registers (not in $s pool)
        TEMP1 = "$t7"
        TEMP2 = "$t6"
        
        # Track scratch register contents to avoid redundant loads within a block
        scratch_state = {TEMP1: None, TEMP2: None}

        # Calculate spill slots ONLY for variables the allocator decided to spill
        spill_offset = {}
        next_slot = 0
        for v in sorted(allocator.spilled):
            spill_offset[v] = next_slot
            next_slot += 4
            
        frame_size = next_slot
        asm = []

        # Allocation Summary (Liveness-aware)
        asm.append("// --- Register Mapping (Liveness-aware) ---")
        rev_map = {}
        for v, r in reg_map.items():
            rev_map.setdefault(r, []).append(v)
        for r in sorted(rev_map.keys()):
            vars_list = ", ".join(sorted(rev_map[r]))
            asm.append(f"// {r}: {vars_list}")
        for v in sorted(spill_offset.keys()):
            asm.append(f"// {v}: stack[{spill_offset[v]}($sp)]")
        asm.append("// ---------------------------")

        asm.append(".text")
        asm.append(".globl main")
        asm.append("main:")

        if frame_size > 0:
            asm.append(f"  ADDI $sp, $sp, -{frame_size}")

        def get_reg(v, scratch):
            """Returns (register_name, load_code). Uses state tracking to eliminate redundant loads."""
            # Case 1: Literal Constant
            try:
                val = float(v)
                if val.is_integer(): val = int(val)
                if scratch_state[scratch] == str(val):
                    return scratch, []
                scratch_state[scratch] = str(val)
                return scratch, [f"  LI {scratch}, {val}"]
            except ValueError: pass

            # Case 2: Permanent Register Assignment
            if v in reg_map:
                return reg_map[v], []

            # Case 3: Spilled Variable
            if v in spill_offset:
                off = spill_offset[v]
                if scratch_state[scratch] == f"mem_{off}":
                    return scratch, []
                scratch_state[scratch] = f"mem_{off}"
                return scratch, [f"  LW {scratch}, {off}($sp)"]

            # Case 4: Ephemeral/Unallocated (e.g. dead or short-lived temp)
            # Correctness fix: We no longer inject a default 'LI 0' as it masks semantic bugs.
            # If the allocator missed a variable, it should be obvious in the assembly.
            scratch_state[scratch] = None
            return scratch, [f"// WARNING: {v} used but not allocated (check DSE)"]

        def store_val(dest, src_reg):
            """Writes a value from a register into the target variable's home."""
            if dest in reg_map:
                if reg_map[dest] != src_reg:
                    return [f"  MOVE {reg_map[dest]}, {src_reg}"]
                return []
            if dest in spill_offset:
                off = spill_offset[dest]
                # Invalidate scratch if we overwrite its underlying memory
                for k in scratch_state:
                    if scratch_state[k] == f"mem_{off}": scratch_state[k] = None
                return [f"  SW {src_reg}, {off}($sp)"]
            return []

        for line in optimized_tac:
            line_clean = line.split("//")[0].strip()
            if not line_clean: continue
            
            # Invalidate state on labels and control flow to prevent stale values
            # propagating across basic block boundaries.
            if line_clean.endswith(":") or line_clean.startswith("goto") or line_clean.startswith("ifFalse"):
                scratch_state[TEMP1] = None
                scratch_state[TEMP2] = None

            if line_clean.endswith(":"):
                asm.append(line_clean)
                continue

            parts = line_clean.split(" ")
            
            if parts[0] == "goto":
                asm.append(f"  J {parts[1]}")
                continue

            if parts[0] == "ifFalse":
                r_cond, loads = get_reg(parts[1], TEMP1)
                asm.extend(loads)
                asm.append(f"  BEQ {r_cond}, $zero, {parts[3]}")
                continue

            if len(parts) >= 3 and parts[1] == "=":
                dest = parts[0]
                
                # Binary Operation: x = y op z
                if len(parts) == 5:
                    left, op, right = parts[2], parts[3], parts[4]
                    is_num = lambda x: x.replace('-','',1).replace('.','',1).isdigit()
                    
                    # ADDI optimization
                    if op == '+' and is_num(right):
                        r_l, lds = get_reg(left, TEMP1)
                        asm.extend(lds)
                        d_reg = reg_map.get(dest, TEMP1)
                        asm.append(f"  ADDI {d_reg}, {r_l}, {right}")
                        asm.extend(store_val(dest, d_reg))
                    elif op == '-' and is_num(right):
                        r_l, lds = get_reg(left, TEMP1)
                        asm.extend(lds)
                        d_reg = reg_map.get(dest, TEMP1)
                        val = int(float(right))
                        asm.append(f"  ADDI {d_reg}, {r_l}, {-val}")
                        asm.extend(store_val(dest, d_reg))
                    elif op == '/':
                        r_l, lds1 = get_reg(left, TEMP1)
                        r_r, lds2 = get_reg(right, TEMP2)
                        asm.extend(lds1)
                        asm.extend(lds2)
                        # Runtime safety check for div-by-zero
                        asm.append(f"  BEQ {r_r}, $zero, div_error")
                        asm.append(f"  DIV {r_l}, {r_r}")
                        d_reg = reg_map.get(dest, TEMP1)
                        asm.append(f"  MFLO {d_reg}")
                        asm.extend(store_val(dest, d_reg))
                    elif op in ('<', '>', '==', '!=', '<=', '>='):
                        r_l, lds1 = get_reg(left, TEMP1)
                        r_r, lds2 = get_reg(right, TEMP2)
                        asm.extend(lds1)
                        asm.extend(lds2)
                        d_reg = reg_map.get(dest, TEMP1)
                        
                        if op == '<':
                            asm.append(f"  SLT {d_reg}, {r_l}, {r_r}")
                        elif op == '>':
                            asm.append(f"  SLT {d_reg}, {r_r}, {r_l}")
                        elif op == '<=':
                            # !(left > right)
                            asm.append(f"  SLT {d_reg}, {r_r}, {r_l}")
                            asm.append(f"  XORI {d_reg}, {d_reg}, 1")
                        elif op == '>=':
                            # !(left < right)
                            asm.append(f"  SLT {d_reg}, {r_l}, {r_r}")
                            asm.append(f"  XORI {d_reg}, {d_reg}, 1")
                        elif op == '==':
                             asm.append(f"  SUB {d_reg}, {r_l}, {r_r}")
                             asm.append(f"  SLTIU {d_reg}, {d_reg}, 1")
                        elif op == '!=':
                             asm.append(f"  SUB {d_reg}, {r_l}, {r_r}")
                             asm.append(f"  SLTU {d_reg}, $zero, {d_reg}")
                        
                        asm.extend(store_val(dest, d_reg))
                    else:
                        m_op = {'+':'ADD', '-':'SUB', '*':'MUL'}.get(op, 'ADD')
                        r_l, lds1 = get_reg(left, TEMP1)
                        r_r, lds2 = get_reg(right, TEMP2)
                        asm.extend(lds1)
                        asm.extend(lds2)
                        d_reg = reg_map.get(dest, TEMP1)
                        asm.append(f"  {m_op} {d_reg}, {r_l}, {r_r}")
                        asm.extend(store_val(dest, d_reg))

                # Simple Assignment: x = y
                elif len(parts) == 3:
                    src = parts[2]
                    r_s, lds = get_reg(src, TEMP1)
                    asm.extend(lds)
                    asm.extend(store_val(dest, r_s))
                
                # Function call: x = call f, arg
                elif parts[2] == "call":
                    r_arg, lds = get_reg(parts[4], TEMP1)
                    asm.extend(lds)
                    asm.append(f"  MOVE $a0, {r_arg}")
                    asm.append(f"  JAL {parts[3].replace(',', '')}")
                    asm.extend(store_val(dest, "$v0"))

        # Program epilogue
        asm.append("main_exit:")
        if frame_size > 0:
            asm.append(f"  ADDI $sp, $sp, {frame_size}")
        asm.append("  LI $v0, 10")
        asm.append("  syscall")
        
        # Division error path
        asm.append("div_error:")
        asm.append("  LI $v0, 10")
        asm.append("  syscall")
        
        return self._peephole_optimize_asm(asm)


def compile_code(source_code, k_regs=4):
    global parse_errors
    parse_errors = []
    
    # Reset lexer state
    lexer.lineno = 1
    
    ast = parser.parse(source_code, lexer=lexer)
    
    # If parsing totally failed
    if not ast:
        return {
            "tree": None,
            "symbol_table": {},
            "raw_tac": [],
            "optimized_tac": [],
            "assembly": [],
            "cfg": None,
            "errors": parse_errors
        }
        
    engine = CompilerEngine()
    engine.analyze_and_gen(ast)
    
    opt_tac = engine.optimize_tac()
    
    asm = engine.generate_assembly(opt_tac, k_regs=k_regs)
    
    # Generate CFG mapping for Frontend Dagre-D3
    cfg = ControlFlowGraph(opt_tac)
    cfg_nodes = []
    cfg_edges = []
    for b_id, bb in cfg.blocks.items():
        label_text = "\\n".join(bb.tac).strip()
        if not label_text: label_text = "(empty)"
        cfg_nodes.append({"id": b_id, "label": label_text})
        for succ in bb.succs:
            cfg_edges.append({"from": b_id, "to": succ})
    
    cfg_data = {
        "nodes": cfg_nodes,
        "edges": cfg_edges,
        "entry": cfg.entry_node
    }
    
    # Rebuild symbol table: keep only variables that still appear
    # as LHS assignments in the final optimized TAC.  This prunes
    # stale entries from dead-code-eliminated or unreachable code.
    surviving_vars = set()
    for line in opt_tac:
        parts = line.split(" ")
        if len(parts) >= 3 and parts[1] == "=":
            surviving_vars.add(parts[0])
    
    # Inject post-optimization values for surviving variables
    for line in opt_tac:
        parts = line.split(" ")
        if len(parts) >= 3 and parts[1] == "=":
            dest = parts[0]
            val_str = " ".join(parts[2:])
            if dest in engine.symbol_table:
                engine.symbol_table[dest]["value"] = val_str
                
    # Prune: remove temporaries and variables no longer in final TAC
    for dest in list(engine.symbol_table.keys()):
        is_temp = len(dest) > 1 and dest[0] == 't' and dest[1:].isdigit()
        if is_temp or dest not in surviving_vars:
            del engine.symbol_table[dest]
    
    errors = parse_errors + engine.semantic_errors
    
    return {
        "tree": ast.to_dict(),
        "symbol_table": engine.symbol_table,
        "raw_tac": engine.tac,
        "optimized_tac": opt_tac,
        "assembly": asm,
        "cfg": cfg_data,
        "errors": errors
    }
