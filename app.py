# server.py
from flask import Flask, request, jsonify
import tempfile
import os
from voetuor_processor import processar_voetuor
from scdp_processor import processar_scdp

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Servidor Voetuor/SCDP ativo"}), 200

@app.route('/processar', methods=['POST'])
def processar_pdfs():
    voetuor_file = request.files.get('voetuor')
    scdp_file = request.files.get('scdp')

    if not voetuor_file or not scdp_file:
        return jsonify({"error": "Envie os dois PDFs: voetuor e scdp"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        voetuor_path = os.path.join(tmpdir, "voetuor.pdf")
        scdp_path = os.path.join(tmpdir, "scdp.pdf")
        voetuor_file.save(voetuor_path)
        scdp_file.save(scdp_path)

        # chama suas funções (retornam estruturas Python)
        voetuor_data = processar_voetuor(voetuor_path)
        scdp_data = processar_scdp(scdp_path)

    return jsonify({
        "voetuor": voetuor_data,
        "scdp": scdp_data,
        "status": "ok"
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Usar bind 0.0.0.0 para Render
    app.run(host="0.0.0.0", port=port)
