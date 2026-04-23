from cfg_impl import ControlFlowGraph

class LICMOptimizer:
    def __init__(self, cfg):
        self.cfg = cfg
        self.changed = False
        
    def get_loop_blocks(self, header, tails):
        loop_blocks = {header}
        stack = []
        for t in tails:
            if t not in loop_blocks:
                loop_blocks.add(t)
                stack.append(t)
        
        while stack:
            n = stack.pop()
            for p in self.cfg.blocks[n].preds:
                if p not in loop_blocks:
                    loop_blocks.add(p)
                    stack.append(p)
        return loop_blocks
        
    def optimize(self):
        # Find loops
        loops = {} # header -> set of tails
        for n in self.cfg.blocks:
            for succ in self.cfg.blocks[n].succs:
                if succ in self.cfg.blocks[n].dom:
                    if succ not in loops: loops[succ] = set()
                    loops[succ].add(n)
                    
        for header, tails in loops.items():
            loop_blocks = self.get_loop_blocks(header, tails)
            
            # Find all variables assigned in the loop
            assigned_in_loop = set()
            for b_id in loop_blocks:
                for line in self.cfg.blocks[b_id].tac:
                    parts = line.split(" ")
                    if len(parts) >= 3 and parts[1] == '=':
                        assigned_in_loop.add(parts[0])
                        
            # Find loop-invariant instructions and hoist them
            # Preheader is the predecessor of header not in loop_blocks
            ph_id = None
            for p in self.cfg.blocks[header].preds:
                if p not in loop_blocks:
                    ph_id = p
                    break
                    
            if not ph_id:
                continue # No preheader exists? Shouldn't happen with normalization
                
            ph = self.cfg.blocks[ph_id]
            
            # Iterate through blocks and hoist
            for b_id in loop_blocks:
                bb = self.cfg.blocks[b_id]
                new_tac = []
                for line in bb.tac:
                    parts = line.split(" ")
                    if len(parts) == 5 and parts[1] == '=' and parts[2] != 'call':
                        dest, left, op, right = parts[0], parts[2], parts[3], parts[4]
                        
                        # Check invariance
                        invariant = True
                        if left in assigned_in_loop: invariant = False
                        if right in assigned_in_loop: invariant = False
                        
                        if invariant:
                            # HOIST!
                            print(f"Hoisting {line} to preheader {ph_id}")
                            # Insert before the final branch of preheader
                            insert_idx = len(ph.tac)
                            if ph.tac and (ph.tac[-1].startswith("goto") or ph.tac[-1].startswith("ifFalse")):
                                insert_idx -= 1
                            ph.tac.insert(insert_idx, line)
                            self.changed = True
                            # The temporary is now defined OUTSIDE the loop. 
                            # Since it's SSA-like, this is perfectly safe. 
                            # We don't append it to new_tac.
                            continue
                            
                    new_tac.append(line)
                bb.tac = new_tac
        return self.changed

if __name__ == "__main__":
    tac = [
        "a = 5",
        "L1:",
        "ifFalse a > 0 goto L2",
        "t1 = 10 * 20", # Invariant!
        "t2 = a - 1",
        "a = t2",
        "goto L1",
        "L2:",
        "return a"
    ]
    cfg = ControlFlowGraph(tac)
    opt = LICMOptimizer(cfg)
    opt.optimize()
    print("\\nFlattened:")
    for line in cfg.flatten():
        print(line)
print("succs of L1:", cfg.blocks["L1"].succs)
