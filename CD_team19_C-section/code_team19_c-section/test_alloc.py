class GraphColoringAllocator:
    def __init__(self, tac_list, k=3):
        self.tac_list = tac_list
        self.k = k
        self.reg_map = {}
        self.spilled = set()
        self.interference = {}
        
    def allocate(self):
        # 1. Instruction Level CFG
        succs = {i: set() for i in range(len(self.tac_list))}
        labels = {}
        for i, line in enumerate(self.tac_list):
            if line.endswith(":"):
                labels[line[:-1]] = i
                
        for i, line in enumerate(self.tac_list):
            if line.startswith("goto "):
                target = line.split(" ")[1]
                if target in labels: succs[i].add(labels[target])
            elif line.startswith("ifFalse "):
                target = line.split(" ")[-1]
                if target in labels: succs[i].add(labels[target])
                if i + 1 < len(self.tac_list): succs[i].add(i + 1)
            elif line.startswith("return "):
                pass
            else:
                if i + 1 < len(self.tac_list): succs[i].add(i + 1)
                
        # 2. Def and Use sets for each instruction
        USE = {}
        DEF = {}
        for i, line in enumerate(self.tac_list):
            u, d = set(), set()
            parts = line.split(" ")
            if len(parts) >= 3 and parts[1] == '=':
                d.add(parts[0])
                for j in range(2, len(parts)):
                    try: float(parts[j])
                    except ValueError:
                        if parts[j] not in ("call",):
                            u.add(parts[j])
            elif line.startswith("ifFalse "):
                try: float(parts[1])
                except ValueError: u.add(parts[1])
            elif line.startswith("return "):
                try: float(parts[1])
                except ValueError: u.add(parts[1])
            USE[i] = u
            DEF[i] = d

        # 3. Liveness Analysis (IN and OUT sets)
        IN = {i: set() for i in range(len(self.tac_list))}
        OUT = {i: set() for i in range(len(self.tac_list))}
        
        changed = True
        while changed:
            changed = False
            for i in range(len(self.tac_list)-1, -1, -1):
                old_in = IN[i].copy()
                old_out = OUT[i].copy()
                
                # OUT[i] = U (IN[s] for s in succs[i])
                new_out = set()
                for s in succs[i]:
                    new_out.update(IN[s])
                OUT[i] = new_out
                
                # IN[i] = USE[i] U (OUT[i] - DEF[i])
                IN[i] = USE[i].union(OUT[i].difference(DEF[i]))
                
                if IN[i] != old_in or OUT[i] != old_out:
                    changed = True

        # 4. Interference Graph
        # Add nodes
        for u_set in USE.values():
            for v in u_set: self.interference.setdefault(v, set())
        for d_set in DEF.values():
            for v in d_set: self.interference.setdefault(v, set())
            
        # Add edges
        for i in range(len(self.tac_list)):
            live_out = OUT[i]
            for d in DEF[i]:
                for l in live_out:
                    if d != l:
                        self.interference[d].add(l)
                        self.interference.setdefault(l, set()).add(d)

        # 5. Graph Coloring (Chaitin's simplified)
        # Assuming no coalescing for this basic test
        
        uncolored = list(self.interference.keys())
        stack = []
        
        # Simplify & Spill
        while uncolored:
            # find node with degree < k
            candidates = [n for n in uncolored if len([x for x in self.interference[n] if x in uncolored]) < self.k]
            if candidates:
                node = candidates[0]
                uncolored.remove(node)
                stack.append(node)
            else:
                # Need to spill. Heuristic: spill temporaries last if possible? 
                # Better: spill node with highest degree
                spill_candidate = max(uncolored, key=lambda n: len([x for x in self.interference[n] if x in uncolored]))
                uncolored.remove(spill_candidate)
                # We push it onto the stack anyway and hope it can be colored (optimistic coloring)
                # If not, it becomes an actual spill
                stack.append(spill_candidate)

        # Assign colors
        available_colors = [f"R{i+1}" for i in range(self.k)]
        
        while stack:
            n = stack.pop()
            neighbor_colors = {self.reg_map[neighbor] for neighbor in self.interference[n] if neighbor in self.reg_map}
            # Find lowest available color
            color = None
            for c in available_colors:
                if c not in neighbor_colors:
                    color = c
                    break
            
            if color:
                self.reg_map[n] = color
            else:
                self.spilled.add(n)

        return self.reg_map, self.spilled

if __name__ == "__main__":
    tac = [
        "a = 5",
        "b = a + 2",
        "c = a + b",
        "d = c + a",
        "e = c + d",
        "return e"
    ]
    alloc = GraphColoringAllocator(tac, k=3)
    reg, spl = alloc.allocate()
    print("Reg map:", reg)
    print("Spilled:", spl)
