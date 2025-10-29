# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL   = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

if not API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY não encontrada no .env!")

_client = genai.Client(api_key=API_KEY)

def ask_gemini(prompt: str) -> str:
    resp = _client.models.generate_content(
        model=MODEL,
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
    )
    txt = getattr(resp, "output_text", None)
    if not txt and getattr(resp, "candidates", None):
        try:
            txt = resp.candidates[0].content.parts[0].text
        except Exception:
            txt = ""
    return txt or ""

def analyze_fit(job_title: str, company: str, description: str, cv_text: str) -> str:
    prompt = f"""
Você é a Evelyn PRO – Confidente Analítica. Avalie o FIT do currículo para a vaga.
Vaga: {job_title} | Empresa: {company}
Descrição da vaga:
{description}

Currículo (texto):
{cv_text}

Responda com:
- Pontos fortes (bullets)
- Lacunas / O que estudar (bullets)
- Pontuação (0 a 100) + justificativa (1 parágrafo)
- 3 ações imediatas
"""
    return ask_gemini(prompt)

def analyze_salary(job_title: str, company: str, description: str, location: str) -> str:
    prompt = f"""
Estime uma faixa salarial (R$) no Brasil considerando senioridade e mercado.
Vaga: {job_title} | Empresa: {company} | Local: {location}
Descrição:
{description}

Entregue:
- Faixa estimada (R$)
- Sinais que aumentam/diminuem a faixa
- Sugestão de ancoragem
"""
    return ask_gemini(prompt)

def generate_cover_letter(job_title: str, company: str, description: str, cv_text: str, tone: str = "profissional e direta") -> str:
    prompt = f"""
Escreva uma carta de apresentação curta (8-12 linhas), tom {tone}, para a vaga.
Vaga: {job_title} | Empresa: {company}

Descrição:
{description}

Currículo:
{cv_text}

Regras:
- 1 frase inicial de impacto (conecte experiência ao impacto da empresa)
- Cite 2-3 competências com exemplos
- Feche com CTA educado
- Sem floreios excessivos
"""
    return ask_gemini(prompt)

def keywords_from_cv(cv_text: str, job_title_hint: str = "") -> str:
    prompt = f"""
Extraia 8-15 palavras-chave (separadas por vírgula) para busca de vagas online.
Se possível, inclua variações em inglês.
Cargo foco: {job_title_hint}

Currículo:
{cv_text}
"""
    return ask_gemini(prompt)

def job_match_analysis(cv_text: str, job_description: str, job_title: str) -> str:
    prompt = f"""
Analise a compatibilidade entre este currículo e a vaga.
Vaga: {job_title}
Descrição: {job_description}

Currículo:
{cv_text}

Entregue:
- Pontuação de compatibilidade (0 a 100)
- 2 a 4 linhas justificando
"""
    return ask_gemini(prompt)

def adapt_cv_for_job(cv_text: str, job_description: str, job_title: str) -> str:
    prompt = f"""
Você é especialista em RH e ATS.
Reescreva este currículo otimizando para a vaga abaixo.
Inclua palavras-chave e estrutura amigável a ATS, mantendo naturalidade.

Vaga: {job_title}
Descrição:
{job_description}

Currículo original:
{cv_text}

Retorne apenas o novo texto do currículo (sem comentários).
"""
    return ask_gemini(prompt)
