# backend/helpers/gemini_tools.py
# -*- coding: utf-8 -*-
from google.genai.client import Client

def ask_gemini_basic(client: Client, model_name: str, prompt: str) -> str:
    """
    Função genérica e centralizada para chamadas ao Gemini usando a nova arquitetura de Client.
    [cite: 116, 118, 166]
    """
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        # O novo SDK simplifica o acesso ao texto 
        return response.text.strip()
    except Exception as e:
        print(f"Erro em ask_gemini_basic: {e}")
        # Tenta extrair
        try:
            return response.candidates[0].content.parts[0].text.strip()
        except Exception:
             return f"⚠️ Erro ao consultar IA: {e}"

def analyze_fit_for_job(client: Client, model_name: str, job_title: str, description: str, cv_text: str) -> str:
    """Analisa a compatibilidade (FIT) do CV com a vaga."""
    prompt = f"""
    Você é uma IA especialista em RH (ATS).
    Analise a compatibilidade (FIT) entre o currículo abaixo e a vaga.
    
    Vaga: {job_title}
    Descrição da Vaga:
    {description}

    Currículo do Candidato:
    {cv_text}

    Responda em HTML formatado:
    - <h3>Análise de Compatibilidade</h3>
    - <p><strong>Pontuação de Compatibilidade:</strong> (de 0% a 100%)</p>
    - <p><strong>Análise Sincera:</strong> (Um parágrafo curto)</p>
    - <p><strong>Pontos Fortes (Match):</strong></p>
    - <ul><li>(Bullet 1)</li><li>(Bullet 2)</li><li>(Bullet 3)</li></ul>
    - <p><strong>Pontos de Atenção (Gaps):</strong></p>
    - <ul><li>(Bullet 1)</li><li>(Bullet 2)</li></ul>
    """
    return ask_gemini_basic(client, model_name, prompt)

def adapt_cv_for_job(client: Client, model_name: str, job_title: str, description: str, cv_text: str) -> str:
    """Adapta o currículo do usuário para a vaga."""
    prompt = f"""
    Você é uma IA especialista em RH (ATS).
    Adapte o "Currículo Original" para otimizá-lo para a "Vaga" descrita.
    
    REGRAS:
    1.  Mantenha 100% da veracidade do currículo original. NÃO invente experiências.
    2.  Destaque habilidades e palavras-chave da "Vaga" que existem no "Currículo".
    3.  Reorganize o "Resumo Profissional" para focar na vaga.
    4.  Retorne **apenas** o currículo adaptado, em formato de texto simples (para copiar e colar).

    Vaga: {job_title}
    Descrição da Vaga:
    {description}

    Currículo Original:
    {cv_text}
    """
    return ask_gemini_basic(client, model_name, prompt)

def generate_cover_letter_for_job(client: Client, model_name: str, job_title: str, description: str, cv_text: str) -> str:
    """Gera uma carta de apresentação para a vaga."""
    prompt = f"""
    Você é uma IA especialista em RH.
    Crie uma carta de apresentação curta (3 parágrafos), profissional e impactante.
    
    REGRAS:
    1.  Baseie-se 100% no "Currículo".
    2.  Enderece os pontos-chave da "Vaga".
    3.  Seja direto e confiante.

    Vaga: {job_title}
    Descrição da Vaga:
    {description}

    Currículo do Candidato:
    {cv_text}
    
    Retorne a carta em texto simples.
    """
    return ask_gemini_basic(client, model_name, prompt)