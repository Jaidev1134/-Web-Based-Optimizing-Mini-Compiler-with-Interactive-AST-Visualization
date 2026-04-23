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
        self.blocks = {} # id -> BasicBlock
        self.entry_node = "B0"
        self._build()
        if self.blocks:
            self._compute_dominators()
            self._insert_preheaders()

    def _build(self):
        leaders = {0: "B0"}
        block_counter = 1
        
        # Identify leaders
        for i, line in enumerate(self.tac_list):
            if line.endswith(":"): # Label
                leaders[i] = line[:-1]
            elif line.startswith("goto ") or line.startswith("ifFalse "):
                if i + 1 < len(self.tac_list):
                    if (i + 1) not in leaders:
                        leaders[i + 1] = f"B{block_counter}"
                        block_counter += 1
                        
        # Create blocks
        sorted_leaders = sorted(leaders.keys())
        for i, start_idx in enumerate(sorted_leaders):
            end_idx = sorted_leaders[i+1] if i + 1 < len(sorted_leaders) else len(self.tac_list)
            b_id = leaders[start_idx]
            bb = BasicBlock(b_id)
            bb.tac = self.tac_list[start_idx:end_idx]
            self.blocks[b_id] = bb
            
        if not self.blocks:
            return

        self.entry_node = leaders[0]

        # Add edges
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
                # Fallthrough
                if i + 1 < len(sorted_leaders):
                    next_id = leaders[sorted_leaders[i+1]]
                    bb.succs.add(next_id)
                    self.blocks[next_id].preds.add(b_id)
            else:
                # Fallthrough
                if i + 1 < len(sorted_leaders):
                    next_id = leaders[sorted_leaders[i+1]]
                    bb.succs.add(next_id)
                    self.blocks[next_id].preds.add(b_id)

    def _compute_dominators(self):
        nodes = list(self.blocks.keys())
        for n in nodes:
            self.blocks[n].dom = set(nodes)
        
        if self.entry_node in self.blocks:
            self.blocks[self.entry_node].dom = {self.entry_node}
            
        changed = True
        while changed:
            changed = False
            for n in nodes:
                if n == self.entry_node:
                    continue
                
                preds = self.blocks[n].preds
                if not preds:
                    new_dom = {n}
                else:
                    intersect = set(nodes)
                    for p in preds:
                        intersect = intersect.intersection(self.blocks[p].dom)
                    new_dom = {n}.union(intersect)
                    
                if new_dom != self.blocks[n].dom:
                    self.blocks[n].dom = new_dom
                    changed = True

    def _insert_preheaders(self):
        # Find natural loops: back-edge A -> B where B dominates A
        loops = []
        for n in self.blocks:
            for succ in self.blocks[n].succs:
                if succ in self.blocks[n].dom:
                    loops.append((succ, n)) # Header, Tail
                    
        # Sort headers to ensure deterministic preheader injection
        headers = set([h for h, t in loops])
        preheader_count = 0
        
        for header in headers:
            preheader_count += 1
            ph_id = f"PH_{header}_{preheader_count}"
            ph = BasicBlock(ph_id)
            # Add a label so it can be jumped to, then jump to the original header
            ph.tac = [f"{ph_id}:", f"goto {header}"]
            
            # Find all preds of header that are NOT part of the loop (not back-edges)
            # A node is in the loop if it can reach the tail without passing through the header.
            # Simplified: A back-edge is from `tail` to `header`. Any pred that doesn't share this dominance relationship might be outside.
            # Technically, Predecessors of header not dominated by header are entering the loop

            entering_preds = []
            for p in self.blocks[header].preds:
                if header not in self.blocks[p].dom:
                    entering_preds.append(p)
                    
            if not entering_preds:
                continue
                
            self.blocks[ph_id] = ph
            
            # Reroute entering edges to the preheader
            for p in entering_preds:
                self.blocks[p].succs.remove(header)
                self.blocks[p].succs.add(ph_id)
                self.blocks[header].preds.remove(p)
                
                ph.preds.add(p)
                # Rewrite the last line of P if it explicitly targets the header
                pb = self.blocks[p]
                if pb.tac:
                    last_line = pb.tac[-1]
                    if last_line.startswith("goto " + header):
                        pb.tac[-1] = f"goto {ph_id}"
                    elif last_line.startswith("ifFalse ") and last_line.split(" ")[-1] == header:
                        parts = last_line.split(" ")
                        parts[-1] = ph_id
                        pb.tac[-1] = " ".join(parts)
            
            # Connect preheader to header
            ph.succs.add(header)
            self.blocks[header].preds.add(ph_id)

    def flatten(self):
        """Flattens the CFG back into a linear TAC list"""
        # Simple DFS topological sort, respecting fall-through if possible
        visited = set()
        flattened = []
        
        def visit(node_id):
            if node_id in visited:
                return
            visited.add(node_id)
            bb = self.blocks[node_id]
            # Emit code
            # Only add the block label if it's not already in the TAC
            if bb.tac and not bb.tac[0].endswith(":"):
                # Usually it has a label, but B0 might not
                if node_id.startswith("B") or node_id.startswith("PH_"):
                     pass # We don't artificially emit new labels unless they were in source or PH
            
            flattened.extend(bb.tac)
            
            # Recurse. Prioritize fall-through edges for contiguous placement
            # Fall-through is the successor not explicitly named in goto/ifFalse
            explicit_targets = set()
            if bb.tac:
                last_line = bb.tac[-1]
                if last_line.startswith("goto "):
                    explicit_targets.add(last_line.split(" ")[1])
                elif last_line.startswith("ifFalse "):
                    explicit_targets.add(last_line.split(" ")[-1])
            
            fallthrough = None
            for succ in bb.succs:
                if succ not in explicit_targets:
                    fallthrough = succ
                    break
                    
            if fallthrough:
                visit(fallthrough)
                
            for succ in bb.succs:
                if succ != fallthrough:
                    visit(succ)
                    
        visit(self.entry_node)
        return flattened

