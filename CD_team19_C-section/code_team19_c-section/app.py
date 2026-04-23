from __future__ import annotations
from flask import Flask, request, jsonify
import logging
from ply_compiler import compile_code

app = Flask(__name__, static_folder="static", static_url_path="/static")
logging.basicConfig(level=logging.INFO)

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/translate", methods=["POST"])
def translate():
    data = request.get_json(silent=True) or {}
    expr = (data.get("expr") or "").strip()
    if not expr:
        return jsonify({"error":"Expression is required."}), 400
    try:
        k_regs = int(data.get("k_regs", 4))
    except (ValueError, TypeError):
        k_regs = 4
        
    try:
        compiler_output = compile_code(expr, k_regs=k_regs)
        return jsonify(compiler_output)
    except Exception as e:
        app.logger.exception("translate failed")
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
