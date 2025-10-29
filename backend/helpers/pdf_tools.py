# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
from fastapi import HTTPException

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extrai texto de um arquivo PDF enviado em bytes.
    Usa PyMuPDF (fitz) para leitura robusta e faz limpeza básica do texto.
    """
    try:
        text = ""
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text("text")

        # limpeza de caracteres estranhos
        text = text.replace("\u0000", "").replace("•", "-")
        text = " ".join(text.split())

        if not text.strip():
            raise HTTPException(status_code=400, detail="PDF vazio ou ilegível")

        return text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {e}")
