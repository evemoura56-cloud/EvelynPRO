# backend/helpers/study.py
# -*- coding: utf-8 -*-
import json
from typing import List, Optional
from ddgs import DDGS
from google.genai.client import Client
from .gemini_tools import ask_gemini_basic # Importação relativa

def web_brief_search(topic: str, max_results:int=5) -> str:
    """Busca breve no DuckDuckGo para montar um resumo factual quando não há PDF."""
    out = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(f'"{topic}" explicação resumida site:(.edu OR wikipedia.org OR .gov)', max_results=max_results):
                t = r.get("title","")
                h = r.get("href","")
                b = r.get("body","")
                if t and h:
                    out.append(f"- {t} — {h}\n  {b[:180]}...")
    except Exception:
        pass
    return "\n".join(out[:max_results])

def build_freire_prompt(subject: str, interests: List[str], base_text: Optional[str]) -> str:
    interests_str = ", ".join(interests) if interests else "sem preferência declarada"
    
    if base_text and len(base_text) > 100:
        topic_header = f"TEMA DE ESTUDO: {subject}\nBASE DO CONTEÚDO: Análise do documento PDF fornecido."
    else:
        topic_header = f"TEMA DE ESTUDO: {subject}\nBASE DO CONTEÚDO: Pesquisa na web sobre o tema."

    return f"""
Você é uma educadora inspirada em Paulo Freire. Construa um aprendizado DIALÓGICO, contextualizado ao mundo do estudante.

REGRAS:
- Explique de forma clara, progressiva e crítica.
- Relacione o conteúdo com os INTERESSES do aluno: {interests_str}.
- Use analogias do cotidiano (séries, músicas, futebol, moda, tecnologia etc) sem perder rigor.
- Divida em etapas: 1) Aquecimento, 2) Conceitos-chave, 3) Analogias pelos interesses, 4) Exercícios práticos, 5) Projeto-aplicação, 6) Checagem de compreensão.
- Sempre proponha pelo menos 3 perguntas abertas.

{topic_header}

ENTREGA (em HTML enxuto, com <h3>, <ul>, <li>, <b> quando fizer sentido):
- Mostre um plano de estudo.
- Traga exemplos específicos alinhados aos interesses.
- Feche com “Próximo passo” e “Como medir progresso”.
"""

def generate_study_plan(client: Client, model_name: str, subject: str, interests: List[str], pdf_text: Optional[str]) -> str:
    """Gera o plano de estudos usando a nova arquitetura de client."""
    base = pdf_text or web_brief_search(subject)
    prompt = build_freire_prompt(subject, interests, base)
    
    # Chama o helper refatorado
    text = ask_gemini_basic(client, model_name, prompt)
    return text