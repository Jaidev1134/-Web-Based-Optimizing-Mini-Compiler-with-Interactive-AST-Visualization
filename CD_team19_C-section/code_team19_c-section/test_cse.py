import sys
sys.path.append(".")
import ply_compiler
res = ply_compiler.compile_code("a = 5; b = a * 2; c = a * 2; d = c + b;")
print(res["optimized_tac"])
