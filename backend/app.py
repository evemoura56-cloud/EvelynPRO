# backend/app.py
# -*- coding: utf-8 -*-
import os
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai  # Importação CORRETA 
import fitz  # PyMuPDF

# Importar helpers
from helpers.job_search import search_jobs_on_web, match_jobs_with_cv
from helpers.study import generate_study_plan
from helpers.pdf_tools import extract_text_from_pdf
from helpers.gemini_tools import (
    ask_gemini_basic,
    analyze_fit_for_job,
    adapt_cv_for_job,
    generate_cover_letter_for_job
)

# ================== CONFIGURAÇÕES BÁSICAS ==================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash") # Nome do modelo [cite: 166]
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 5000))
DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
os.makedirs(DATA_DIR, exist_ok=True)

if not API_KEY:
    raise ValueError("⚠️ GOOGLE_API_KEY não encontrada. Verifique o .env")

# Configuração do App Flask
app = Flask(__name__, template_folder="../templates", static_folder="../static")
CORS(app)

# Inicializa cliente do Gemini (Nova arquitetura) 
g_client = genai.Client(api_key=API_KEY)

# ================== ROTAS PRINCIPAIS ==================

@app.route("/")
def home():
    """Renderiza a página principal."""
    return render_template("index.html")

# ===== CHAT PADRÃO =====
@app.post("/api/chat")
def api_chat():
    """Rota de chat genérico."""
    data = request.get_json(force=True)
    prompt = data.get("prompt", "")
    
    try:
        persona_path = os.path.join(os.path.dirname(__file__), "persona_system_prompt.txt")
        with open(persona_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception:
        system_prompt = "Você é a Evelyn PRO, uma IA assistente de carreira e estudos."

    full_prompt = f"{system_prompt}\n\nUsuário perguntou: {prompt}"
    resp = ask_gemini_basic(g_client, MODEL, full_prompt) # Passa client e model
    return jsonify({"ia_response": resp})

# ===== UPLOAD DE CURRÍCULO =====
@app.post("/api/upload_cv")
def api_upload_cv():
    """Processa o upload do CV e salva o texto."""
    try:
        user_id = request.args.get("user_id", "anon")
        if "cv_file" not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado", "ok": False}), 400
            
        file = request.files["cv_file"]
        pdf_bytes = file.read()
        text = extract_text_from_pdf(pdf_bytes)
        
        cv_path = os.path.join(DATA_DIR, f"{user_id}_cv.txt")
        with open(cv_path, "w", encoding="utf-8") as f:
            f.write(text)

        prompt = f"""
        Você é uma Coach de Carreira analítica e sincera.
        Analise este currículo e forneça uma resposta formatada em Markdown simples:
        1.  **Pontos Fortes:** (2-3 bullets)
        2.  **Pontos a Melhorar:** (2-3 bullets, com sugestões práticas)
        3.  **Áreas e Cargos Compatíveis:** (Liste 3-4 áreas)

        CURRÍCULO:
        {text}
        """
        resumo = ask_gemini_basic(g_client, MODEL, prompt) # Passa client e model
        
        return jsonify({
            "cv_text": text,
            "cv_analysis_summary": resumo
        })
    except Exception as e:
        return jsonify({"error": f"Erro no upload: {e}", "ok": False}), 500

# ===== BUSCAR VAGAS =====
@app.post("/api/find_jobs")
def find_jobs():
    """Busca vagas com base nos filtros do formulário."""
    data = request.get_json(force=True)
    
    jobs = search_jobs_on_web(
        job_title=data.get("cargo", ""),
        estado=data.get("estado", ""),
        cidade=data.get("cidade", ""),
        modelo=data.get("modelo", ""),
        tipo=data.get("tipo", ""),
        timelimit='w'
    )
    
    if not jobs:
        return jsonify({"ok": True, "jobs": [], "message": "Nenhuma vaga encontrada 😕"})

    return jsonify({"ok": True, "jobs": jobs})

@app.post("/api/match_jobs")
def match_jobs():
    """Busca vagas com base no CV do usuário."""
    data = request.get_json(force=True)
    user_id = data.get("user_id", "anon")
    
    cv_path = os.path.join(DATA_DIR, f"{user_id}_cv.txt")
    if not os.path.exists(cv_path):
        return jsonify({"ok": False, "error": "⚠️ Faça o upload do seu currículo antes de buscar vagas que dão match!"})

    with open(cv_path, "r", encoding="utf-8") as f:
        cv_text = f.read()

    # Passa g_client e MODEL
    results = match_jobs_with_cv(g_client, MODEL, cv_text, data.get("cargo", ""))
    
    if not results:
        return jsonify({"ok": True, "jobs": [], "message": "Nenhuma vaga compatível encontrada 😕"})

    return jsonify({"ok": True, "jobs": results})

# ===== AÇÕES DAS VAGAS =====

def get_cv_text(user_id="anon"):
    """Helper para carregar o CV do usuário."""
    cv_path = os.path.join(DATA_DIR, f"{user_id}_cv.txt")
    if not os.path.exists(cv_path):
        raise FileNotFoundError("Currículo não encontrado. Faça o upload primeiro.")
    with open(cv_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/job_fit")
def api_job_fit():
    """Analisa a compatibilidade (FIT) entre o CV e a vaga."""
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id", "anon")
        job_desc = data.get("job_description", "")
        job_title = data.get("job_title", "")
        cv_text = get_cv_text(user_id)
        
        result = analyze_fit_for_job(g_client, MODEL, job_title, job_desc, cv_text)
        return jsonify({"analysis": result})
    except Exception as e:
        return jsonify({"error": str(e), "ok": False}), 500

@app.post("/api/adapt_cv")
def api_adapt_cv():
    """Adapta o CV para a vaga."""
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id", "anon")
        job_desc = data.get("job_description", "")
        job_title = data.get("job_title", "")
        cv_text = get_cv_text(user_id)
        
        adapted = adapt_cv_for_job(g_client, MODEL, job_title, job_desc, cv_text)
        return jsonify({"adapted_cv": adapted})
    except Exception as e:
        return jsonify({"error": str(e), "ok": False}), 500

@app.post("/api/generate_cover_letter")
def api_cover_letter():
    """Gera uma carta de apresentação."""
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id", "anon")
        job_desc = data.get("job_description", "")
        job_title = data.get("job_title", "")
        cv_text = get_cv_text(user_id)
        
        letter = generate_cover_letter_for_job(g_client, MODEL, job_title, job_desc, cv_text)
        return jsonify({"cover_letter": letter})
    except Exception as e:
        return jsonify({"error": str(e), "ok": False}), 500

# ===== ROTA DE ESTUDOS =====
@app.post("/api/study")
def study():
    """Rota de estudos no método Paulo Freire."""
    subject = None
    interests = []
    pdf_text = None
    
    try:
        if request.files.get("pdf"):
            subject = request.values.get("subject", "Conteúdo do PDF")
            interests_json = request.values.get("interests", "[]")
            interests = json.loads(interests_json)
            
            f = request.files["pdf"]
            pdf_bytes = f.read()
            pdf_text = extract_text_from_pdf(pdf_bytes)
        
        elif request.is_json:
            data = request.get_json(force=True)
            subject = data.get("subject", "").strip()
            interests = data.get("interests", [])
            
        if not subject:
            return jsonify({"ok": False, "error": "Informe o 'subject' (tema)"}), 400

        html = generate_study_plan(g_client, MODEL, subject, interests, pdf_text)
        return jsonify({"ok": True, "study_plan": html})
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ================== EXECUÇÃO ==================
if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)