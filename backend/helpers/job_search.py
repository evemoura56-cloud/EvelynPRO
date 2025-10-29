# -*- coding: utf-8 -*-
import os
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

# ===================== BUSCA MELHORADA =====================
def search_jobs_on_web(job_title: str, location: str = "Brasil", max_results: int = 8):
    """
    Busca vagas REAIS e com descrição curta.
    Filtra sites genéricos e tenta trazer vagas únicas (não páginas de listagens).
    """
    try:
        # Busca mais específica e refinada
        query = (
            f'"{job_title}" vaga emprego contratação site:(gupy.io OR infojobs.com.br OR trampos.co OR vagas.com.br) {location}'
        )

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results * 2):
                title = r.get("title", "")
                body = r.get("body", "")
                href = r.get("href", "")

                # Filtra páginas genéricas (como "30 mil vagas")
                if any(palavra in title.lower() for palavra in [
                    "mil vagas", "principais vagas", "as +", "vagas de analista em:", "linkedin", "catho"
                ]):
                    continue

                # Mantém apenas descrições curtas e links válidos
                if href and len(body) > 60:
                    results.append({
                        "title": title.strip(),
                        "href": href.strip(),
                        "body": body.strip()
                    })

        # Limita o retorno final
        return results[:max_results]

    except Exception as e:
        print(f"Erro na busca de vagas: {e}")
        return []

# ===================== MATCH COM O CURRÍCULO =====================
def match_jobs_with_cv(cv_text: str, job_title: str = ""):
    """
    Busca vagas e analisa compatibilidade com o currículo do usuário.
    """
    try:
        jobs = search_jobs_on_web(job_title or "emprego", max_results=6)
        if not jobs:
            print("Nenhuma vaga encontrada.")
            return []

        matched = []
        for job in jobs:
            vaga = job.get("body", "")
            link = job.get("href", "")
            titulo = job.get("title", "Vaga sem título")

            prompt = f"""
Você é uma IA especialista em recrutamento. Compare o seguinte currículo com a vaga abaixo e diga:

- Uma **pontuação de compatibilidade (0 a 100)**
- Um **resumo técnico objetivo (em até 2 linhas)** explicando o motivo da nota.
- Use uma linguagem profissional, mas direta.

### Currículo:
{cv_text}

### Vaga:
{vaga}
"""

            response = gclient.models.generate_content(
                model=MODEL,
                contents=[{"role": "user", "parts": [{"text": prompt}]}]
            )

            if hasattr(response, "candidates") and response.candidates:
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
        print("Erro em match_jobs_with_cv:", e)
        return []
