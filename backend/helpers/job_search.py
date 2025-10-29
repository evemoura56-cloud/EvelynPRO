# -*- coding: utf-8 -*-
import os
import re
from dotenv import load_dotenv
from ddgs import DDGS
from google import genai

# ===================== CONFIG =====================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

if not API_KEY:
    raise ValueError("⚠️ GOOGLE_API_KEY não encontrada. Verifique seu arquivo .env.")

gclient = genai.Client(api_key=API_KEY)

# ===================== BUSCA DE VAGAS REAIS =====================
def search_jobs_on_web(job_title: str, location: str = "Brasil", max_results: int = 8):
    """
    Busca vagas REAIS e ignora páginas genéricas de sites de emprego.
    Retorna apenas resultados com links diretos para vagas.
    """
    padrao_vagas = re.compile(
        r"(infojobs\.com\.br/vaga-de-|vagas\.com\.br/vagas/|linkedin\.com/jobs/view/|catho\.com\.br/vagas/|gupy\.io/)",
        re.IGNORECASE,
    )

    try:
        query = (
            f'"{job_title}" vaga emprego contratação site:(infojobs.com.br OR vagas.com.br OR linkedin.com/jobs OR catho.com.br OR gupy.io) {location}'
        )

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results * 2):
                title = r.get("title", "")
                body = r.get("body", "")
                href = r.get("href", "")

                if href and padrao_vagas.search(href) and len(body) > 40:
                    results.append({
                        "title": title.strip(),
                        "href": href.strip(),
                        "body": body.strip()
                    })
                if len(results) >= max_results:
                    break

        return results

    except Exception as e:
        print(f"Erro na busca de vagas: {e}")
        return []

# ===================== ANÁLISE DE MATCH COM O CURRÍCULO =====================
def match_jobs_with_cv(cv_text: str, job_title: str = ""):
    """
    Busca vagas REAIS e analisa compatibilidade com o currículo.
    Retorna título, link e análise de compatibilidade.
    """
    try:
        jobs = search_jobs_on_web(job_title or "emprego", max_results=5)
        if not jobs:
            print("Nenhuma vaga encontrada.")
            return [{"title": "Nenhuma vaga compatível encontrada 😕"}]

        matched = []
        for job in jobs:
            vaga = job.get("body", "")
            link = job.get("href", "")
            titulo = job.get("title", "Vaga sem título")

            prompt = f"""
Você é uma IA especialista em recrutamento. Compare o seguinte currículo com a vaga abaixo e gere:

1. Uma **pontuação de compatibilidade (0 a 100)**.
2. Um **resumo técnico objetivo (em até 3 linhas)** justificando a nota.

Mantenha o texto bem formatado em Markdown (use negrito e quebras de linha).

### Currículo:
{cv_text}

### Vaga:
{vaga}
"""

            response = gclient.models.generate_content(
                model=MODEL,
                contents=[{"role": "user", "parts": [{"text": prompt}]}]
            )

            # Corrige para o novo formato de resposta da API
            if hasattr(response, "text"):
                text = response.text.strip()
            elif hasattr(response, "output_text"):
                text = response.output_text.strip()
            elif hasattr(response, "candidates"):
                part = response.candidates[0].content.parts[0]
                text = getattr(part, "text", "").strip()
            else:
                text = "⚠️ Sem resposta da IA"

            matched.append({
                "title": titulo,
                "href": link,
                "analysis": text
            })

        return matched

    except Exception as e:
        print(f"Erro em match_jobs_with_cv: {e}")
        return [{"title": "Erro ao processar compatibilidade 😞", "analysis": str(e)}]
