# -*- coding: utf-8 -*-
import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from helpers.job_search import search_jobs_on_web, match_jobs_with_cv
from helpers.pdf_tools import extract_text_from_pdf


# ================== CONFIGURAÇÕES BÁSICAS ==================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 5000))
DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
os.makedirs(DATA_DIR, exist_ok=True)

if not API_KEY:
    raise ValueError("⚠️ GOOGLE_API_KEY não encontrada. Verifique o .env")

app = Flask(__name__, template_folder="../templates", static_folder="../static")
CORS(app)

# Inicializa cliente do Gemini
gclient = genai.Client(api_key=API_KEY)

# ================== FUNÇÃO CENTRAL DO GEMINI ==================
def ask_gemini(prompt: str):
    """
    Envia prompt ao modelo Gemini e retorna o texto puro.
    """
    try:
        response = gclient.models.generate_content(
            model=MODEL,
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        # A versão nova do SDK usa .candidates
        if hasattr(response, "candidates") and response.candidates:
            part = response.candidates[0].content.parts[0]
            text = getattr(part, "text", None)
            if text:
                return text.strip()
        return "⚠️ Nenhuma resposta recebida da IA."
    except Exception as e:
        print(f"Erro em ask_gemini: {e}")
        return f"⚠️ Erro ao consultar IA: {e}"

# ================== ROTAS PRINCIPAIS ==================
@app.route("/")
def home():
    return render_template("index.html")

# ===== CHAT PADRÃO =====
@app.post("/api/chat")
def api_chat():
    data = request.get_json(force=True)
    user_id = data.get("user_id", "anon")
    prompt = data.get("prompt", "")
    resp = ask_gemini(f"Usuário ({user_id}) perguntou: {prompt}")
    return jsonify({"ia_response": resp})

# ===== UPLOAD DE CURRÍCULO =====
@app.post("/api/upload_cv")
def api_upload_cv():
    try:
        user_id = request.args.get("user_id", "anon")
        file = request.files["cv_file"]
        pdf_bytes = file.read()
        text = extract_text_from_pdf(pdf_bytes)
        cv_path = os.path.join(DATA_DIR, f"{user_id}_cv.txt")
        with open(cv_path, "w", encoding="utf-8") as f:
            f.write(text)

        resumo = ask_gemini(f"Crie um resumo profissional curto e claro para este currículo:\n{text}")
        return jsonify({
            "cv_text": text,
            "cv_analysis_summary": resumo
        })
    except Exception as e:
        return jsonify({"error": f"Erro no upload: {e}", "ok": False})

# ===== BUSCAR VAGAS =====
@app.post("/api/find_jobs")
def find_jobs():
    data = request.get_json(force=True)
    job_title = data.get("job_title", "")
    location = data.get("location", "Brasil")

    jobs = search_jobs_on_web(job_title, location)
    if not jobs:
        return jsonify({"ok": True, "jobs": [], "message": "Nenhuma vaga encontrada 😕"})

    return jsonify({"ok": True, "jobs": jobs})

@app.post("/api/match_jobs")
def match_jobs():
    data = request.get_json(force=True)
    user_id = data.get("user_id", "anon")
    job_title = data.get("job_title", "")

    cv_path = f"data/{user_id}_cv.txt"
    if not os.path.exists(cv_path):
        return jsonify({"ok": False, "error": "⚠️ Faça o upload do seu currículo antes de buscar vagas que dão match!"})

    with open(cv_path, "r", encoding="utf-8") as f:
        cv_text = f.read()

    results = match_jobs_with_cv(cv_text, job_title)
    if not results:
        return jsonify({"ok": True, "jobs": [], "message": "Nenhuma vaga compatível encontrada 😕"})

    return jsonify({"ok": True, "jobs": results})

# ===== ANÁLISE DE COMPATIBILIDADE =====
@app.post("/api/job_fit")
def api_job_fit():
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id", "anon")
        job_desc = data.get("job_description", "")
        cv_path = os.path.join(DATA_DIR, f"{user_id}_cv.txt")

        if not os.path.exists(cv_path):
            return jsonify({"error": "Currículo não encontrado", "ok": False})

        with open(cv_path, "r", encoding="utf-8") as f:
            cv_text = f.read()

        prompt = f"Compare o seguinte currículo com a descrição da vaga:\n\nCURRÍCULO:\n{cv_text}\n\nVAGA:\n{job_desc}\n\nExplique brevemente o nível de compatibilidade."
        result = ask_gemini(prompt)
        return jsonify({"fit_analysis": result})
    except Exception as e:
        return jsonify({"error": str(e), "ok": False})

# ===== ADAPTAR CURRÍCULO =====
@app.post("/api/adapt_cv")
def api_adapt_cv():
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id", "anon")
        job_desc = data.get("job_description", "")
        cv_path = os.path.join(DATA_DIR, f"{user_id}_cv.txt")

        if not os.path.exists(cv_path):
            return jsonify({"error": "Currículo não encontrado", "ok": False})

        with open(cv_path, "r", encoding="utf-8") as f:
            cv_text = f.read()

        prompt = f"""
Adapte o currículo abaixo para se alinhar à vaga descrita.
Mantenha o tom profissional e insira palavras-chave relevantes.

CURRÍCULO:
{cv_text}

VAGA:
{job_desc}
"""
        adapted = ask_gemini(prompt)
        return jsonify({"adapted_cv": adapted})
    except Exception as e:
        return jsonify({"error": str(e), "ok": False})

# ===== CARTA DE APRESENTAÇÃO =====
@app.post("/api/generate_cover_letter")
def api_cover_letter():
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id", "anon")
        job_desc = data.get("job_description", "")
        cv_path = os.path.join(DATA_DIR, f"{user_id}_cv.txt")

        if not os.path.exists(cv_path):
            return jsonify({"error": "Currículo não encontrado", "ok": False})

        with open(cv_path, "r", encoding="utf-8") as f:
            cv_text = f.read()

        prompt = f"""
Crie uma carta de apresentação profissional e envolvente com base no currículo e vaga abaixo.

CURRÍCULO:
{cv_text}

VAGA:
{job_desc}
"""
        letter = ask_gemini(prompt)
        return jsonify({"generated_cover_letter": letter})
    except Exception as e:
        return jsonify({"error": str(e), "ok": False})

# ================== EXECUÇÃO ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
