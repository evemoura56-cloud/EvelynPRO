# backend/helpers/job_search.py
# -*- coding: utf-8 -*-
import re
from ddgs import DDGS
from google.genai.client import Client
from .gemini_tools import ask_gemini_basic # Importação relativa

# ===================== BUSCA DE VAGAS AVANÇADA =====================
def search_jobs_on_web(job_title: str, estado: str = "", cidade: str = "",
                         modelo: str = "", tipo: str = "", 
                         max_results: int = 8, timelimit: str = 'w'):
    """
    Busca vagas reais em sites (InfoJobs, Vagas, Gupy, Catho, LinkedIn)
    aplicando filtros.
    'timelimit': d (dia), w (semana), m (mês)
    """

    padrao_vagas = re.compile(
        r"(infojobs\.com\.br/vaga-de-|vagas\.com\.br/vagas/|linkedin\.com/jobs/view/|catho\.com\.br/vagas/|gupy\.io/)",
        re.IGNORECASE,
    )

    try:
        filtros = " ".join(filter(None, [estado, cidade, modelo, tipo]))
        query = (
            f'"{job_title}" vaga emprego {filtros} '
            "site:(infojobs.com.br OR vagas.com.br OR linkedin.com/jobs OR catho.com.br OR gupy.io)"
        )

        results = []
        with DDGS() as ddgs:
            # Aplicando o timelimit
            for r in ddgs.text(query, max_results=max_results * 2, timelimit=timelimit):
                title = r.get("title", "")
                body = r.get("body", "")
                href = r.get("href", "")

                if href and padrao_vagas.search(href) and len(body) > 50:
                    results.append({
                        "title": title.strip(),
                        "href": href.strip(),
                        "body": body.strip(),
                    })

                if len(results) >= max_results:
                    break
        
        return results

    except Exception as e:
        print(f"Erro na busca de vagas: {e}")
        return []

# ===================== MATCH COM CURRÍCULO =====================
def match_jobs_with_cv(client: Client, model_name: str, cv_text: str, job_title: str, 
                         estado: str = "", cidade: str = "",
                         modelo: str = "", tipo: str = ""):
    """
    Busca vagas reais e GERA a compatibilidade com o currículo.
    """
    try:
        jobs = search_jobs_on_web(job_title or "vaga",
                                  estado=estado, cidade=cidade,
                                  modelo=modelo, tipo=tipo, 
                                  max_results=5, timelimit='w')

        if not jobs:
            return []

        matched = []
        for job in jobs:
            vaga_desc = job.get("body", "")
            
            prompt = f"""
            Compare o currículo com a vaga e gere uma pontuação (0-100) e 2 linhas de justificativa (em Markdown).

            CURRÍCULO:
            {cv_text}

            VAGA:
            {vaga_desc}
            """
            analysis_text = ask_gemini_basic(client, model_name, prompt)
            
            job["analysis"] = analysis_text
            matched.append(job)

        return matched

    except Exception as e:
        print(f"Erro em match_jobs_with_cv: {e}")
        return []