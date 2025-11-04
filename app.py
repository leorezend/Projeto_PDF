# app.py (Versão Assíncrona)
from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import uuid
import threading
import traceback
from voetuor_processor import processar_voetuor
from scdp_processor import processar_scdp

app = Flask(__name__)
CORS(app)

# Dicionário para armazenar o status das tarefas: {task_id: {"status": "PENDING"|"COMPLETED"|"FAILED", "result": {...} | "error": "..."}}
tasks = {}

def background_process(task_id, voetuor_file, scdp_file):
    """Função que executa o processamento pesado em segundo plano."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            voetuor_path = os.path.join(tmpdir, "voetuor.pdf")
            scdp_path = os.path.join(tmpdir, "scdp.pdf")
            
            # Salva os arquivos temporariamente
            voetuor_file.save(voetuor_path)
            scdp_file.save(scdp_path)

            # Executa o processamento pesado
            voetuor_data = processar_voetuor(voetuor_path)
            scdp_data = processar_scdp(scdp_path)

        # Atualiza o status da tarefa
        tasks[task_id] = {
            "status": "COMPLETED",
            "result": {
                "voetuor": voetuor_data,
                "scdp": scdp_data,
                "status": "ok"
            }
        }

    except Exception as e:
        # Em caso de falha, registra o erro
        print(f"--- ERRO NA TAREFA {task_id} ---")
        traceback.print_exc()
        print("------------------------------------")
        tasks[task_id] = {
            "status": "FAILED",
            "error": str(e)
        }

@app.route('/')
def home():
    return jsonify({"message": "Servidor Voetuor/SCDP ativo"}), 200

@app.route('/start_process', methods=['POST'])
def start_process():
    """Endpoint para iniciar o processamento e retornar um ID de tarefa."""
    voetuor_file = request.files.get('voetuor')
    scdp_file = request.files.get('scdp')

    if not voetuor_file or not scdp_file:
        return jsonify({"error": "Envie os dois PDFs: voetuor e scdp"}), 400

    # Cria um ID único para a tarefa
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "PENDING"}

    # Inicia o processamento em uma thread separada
    thread = threading.Thread(target=background_process, args=(task_id, voetuor_file, scdp_file))
    thread.start()

    # Retorna imediatamente o ID da tarefa (202 Accepted)
    return jsonify({"task_id": task_id, "status": "PENDING"}), 202

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """Endpoint para verificar o status da tarefa."""
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task ID not found"}), 404
    
    if task["status"] == "COMPLETED":
        # Retorna o resultado final
        result = task["result"]
        return jsonify(result), 200
    
    if task["status"] == "FAILED":
        # Retorna o erro
        error_msg = task["error"]
        return jsonify({"status": "FAILED", "error": error_msg}), 500

    # Retorna o status PENDING
    return jsonify({"status": task["status"]}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
