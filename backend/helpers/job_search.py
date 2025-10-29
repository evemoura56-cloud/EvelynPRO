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

# ===================== BUSCA DE VAGAS AVANÇADA =====================
def search_jobs_on_web(job_title: str, estado: str = "", cidade: str = "",
                       modelo: str = "", tipo: str = "", max_results: int = 8):
    """
    Busca vagas reais em sites (InfoJobs, Vagas, Gupy, Catho, LinkedIn)
    aplicando filtros: estado, cidade, modelo (CLT, PJ...) e tipo (home office, etc.)
    """

    padrao_vagas = re.compile(
        r"(infojobs\.com\.br/vaga-de-|vagas\.com\.br/vagas/|linkedin\.com/jobs/view/|catho\.com\.br/vagas/|gupy\.io/)",
        re.IGNORECASE,
    )

    try:
        filtros = " ".join(filter(None, [estado, cidade, modelo, tipo]))
        query = (
            f'"{job_title}" vaga emprego contratação {filtros} '
            "site:(infojobs.com.br OR vagas.com.br OR linkedin.com/jobs OR catho.com.br OR gupy.io)"
        )

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results * 2):
                title = r.get("title", "")
                body = r.get("body", "")
                href = r.get("href", "")

                if href and padrao_vagas.search(href) and len(body) > 50:
                    results.append({
                        "title": title.strip(),
                        "href": href.strip(),
                        "body": body.strip(),
                        "local": f"{cidade or estado or 'Brasil'}",
                        "modelo": modelo or "Não informado",
                        "tipo": tipo or "Não informado"
                    })

                if len(results) >= max_results:
                    break

        return results if results else [{"title": "Nenhuma vaga encontrada 😕"}]

    except Exception as e:
        print(f"Erro na busca de vagas: {e}")
        return [{"title": "Erro ao buscar vagas 😞", "body": str(e)}]

# ===================== MATCH COM CURRÍCULO =====================
def match_jobs_with_cv(cv_text: str, job_title: str = "",
                       estado: str = "", cidade: str = "",
                       modelo: str = "", tipo: str = ""):
    """
    Busca vagas reais com filtros e gera compatibilidade com currículo.
    """
    try:
        jobs = search_jobs_on_web(job_title or "emprego",
                                  estado=estado, cidade=cidade,
                                  modelo=modelo, tipo=tipo, max_results=5)

        if not jobs or not isinstance(jobs, list):
            return [{"title": "Nenhuma vaga encontrada 😕"}]

        matched = []
        for job in jobs:
            vaga = job.get("body", "")
            link = job.get("href", "")
            titulo = job.get("title", "Vaga sem título")

            prompt = f"""
Você é uma IA especialista em recrutamento.
Compare o seguinte currículo com a vaga abaixo e gere:

1️⃣ Uma **pontuação de compatibilidade (0 a 100)**.  
2️⃣ Um **resumo técnico objetivo (em até 3 linhas)** justificando a nota.  
3️⃣ Linguagem direta, profissional e leve.

### Currículo:
{cv_text}

### Vaga:
{vaga}
"""

            response = gclient.models.generate_content(
                model=MODEL,
                contents=[{"role": "user", "parts": [{"text": prompt}]}]
            )

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
                "local": f"{cidade or estado or 'Brasil'}",
                "modelo": modelo or "Não informado",
                "tipo": tipo or "Não informado",
                "analysis": text
            })

        return matched

    except Exception as e:
        print(f"Erro em match_jobs_with_cv: {e}")
        return [{"title": "Erro ao processar compatibilidade 😞", "analysis": str(e)}]
