# interpreters/research/_shared/pdf_parser.py
"""PDF 文本提取"""

import pdfplumber


def extract_text(pdf_path: str, max_pages: int = 3) -> str:
    """
    提取 PDF 前 N 页文本
    
    Args:
        pdf_path: PDF 文件路径
        max_pages: 最大页数
    
    Returns:
        提取的文本
    """
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages[:max_pages]
        texts = []
        for p in pages:
            text = p.extract_text()
            if text:
                texts.append(text)
        return "\n\n".join(texts)
