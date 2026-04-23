from ply_compiler import compile_code, GraphColoringAllocator, ControlFlowGraph

src = """
a = 5;
b = 0;
c = 2;
d = a * 0 + 10 - 10;
e = a * 1 + b * 1 + 0;
f = (3 + 7) * (2 - 1) * (0 + 1);
g = e + f;
h = g - g;
i = a * 2 - 2 * a;
j = (a + b) * 0;

k = 100 / 1;
l = 0 / 5;
m = k + l;

n = 2 ^ 1;
o = 20;
p = o + 0;
q = p * 1;
r = q;
s = r;
t = s;
u = 2 * 3 + 4 * 5;
v = u - 2 * 3;
w = v * 0;
x = x * 1;
y = x - x + a - a;
z = c / b;
"""
res = compile_code(src, 4)
tac = res['optimized_tac']
alloc = GraphColoringAllocator(tac, 4)
alloc.allocate()

for var in ['x', 'y', 'z', 'w']:
    print(f"Interferences for {var}:", alloc.interference.get(var, set()))
