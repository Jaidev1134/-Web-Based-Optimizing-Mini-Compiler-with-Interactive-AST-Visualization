from ply_compiler import compile_code
code_str = '''a = 5; b = 0; c = 2;
d = (a * 0) + (10 - 10);
e = (a * 1) + (b * 1);
f = (3 + 7) * (2 - 1) * (0 + 1);
g = e + f; h = g - g;
i = (a * 2) - (a * 2); j = (a + b) * 0;
k = 100 / 1; l = 0 / 5;
m = k + l;
t1 = 4 * 5; t2 = 20;
if (t1 == t2) { n = 1; } else { n = 2; }
t3 = a - a;
if (t3) { o = 10; } else { o = 20; }
p = o + 0; q = p * 1;
r = q; s = r; t = s;
u = (2 * 3) + (4 * 5); v = u - (2 * 3);
w = v * 0;
x = 10; x = x + 0; x = x * 1;
y = (x - x) + (a - a);
z = c / b;
'''
try:
    res = compile_code(code_str)
    import json
    print("=== SYMBOL TABLE ===")
    print(json.dumps(res['symbol_table'], indent=2))
    print("=== TAC ===")
    print('\n'.join(res['raw_tac'][:10] + ["..."]))
    print("=== MIPS ===")
    print('\n'.join(res['assembly'][:10] + ["..."]))
except Exception as e:
    import traceback
    traceback.print_exc()
