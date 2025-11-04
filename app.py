from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import traceback
import multiprocessing
import time
from voetuor_processor import processar_voetuor
from scdp_processor import processar_scdp

app = Flask(__name__)

# ✅ Permite o acesso do APEX (ajuste se quiser limitar)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- resto do código permanece igual ---


def run_processor(processor_func, pdf_path, queue):
    try:
        data = processor_func(pdf_path)
        queue.put({"status": "COMPLETED", "data": data})
    except Exception as e:
        queue.put({"status": "FAILED", "error": str(e)})

@app.route('/processar_pdfs', methods=['POST'])
def processar_pdfs_endpoint():
    start_time = time.time()
    voetuor_file = request.files.get('voetuor')
    scdp_file = request.files.get('scdp')

    if not voetuor_file or not scdp_file:
        return jsonify({"status": "erro", "mensagem": "Envie os dois PDFs: voetuor e scdp"}), 400

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            voetuor_path = os.path.join(tmpdir, "voetuor.pdf")
            scdp_path = os.path.join(tmpdir, "scdp.pdf")
            voetuor_file.save(voetuor_path)
            scdp_file.save(scdp_path)

            queue_voetuor = multiprocessing.Queue()
            queue_scdp = multiprocessing.Queue()

            p_voetuor = multiprocessing.Process(target=run_processor, args=(processar_voetuor, voetuor_path, queue_voetuor))
            p_scdp = multiprocessing.Process(target=run_processor, args=(processar_scdp, scdp_path, queue_scdp))

            p_voetuor.start()
            p_scdp.start()
            p_voetuor.join()
            p_scdp.join()

            result_voetuor = queue_voetuor.get()
            result_scdp = queue_scdp.get()

            if result_voetuor["status"] == "FAILED" or result_scdp["status"] == "FAILED":
                error_msg = f"Erro Voetuor: {result_voetuor.get('error', 'N/A')}. Erro SCDP: {result_scdp.get('error', 'N/A')}"
                return jsonify({"status": "erro", "mensagem": error_msg}), 500

            end_time = time.time()
            elapsed_time = end_time - start_time

            return jsonify({
                "status": "sucesso",
                "dados": {
                    "voetuor_data": result_voetuor["data"],
                    "scdp_data": result_scdp["data"],
                    "tempo_total": f"{elapsed_time:.4f} segundos"
                }
            }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "erro", "mensagem": f"Erro interno: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
