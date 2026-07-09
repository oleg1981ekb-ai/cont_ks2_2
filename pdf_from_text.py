import os
from typing import List


def _wrap_text(text: str, max_chars: int) -> List[str]:
    """Простейший перенос по длине строки (без ширины шрифта)."""
    words = text.split(" ")
    lines = []
    cur = ""

    for w in words:
        if not cur:
            cur = w
            continue
        if len(cur) + 1 + len(w) <= max_chars:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_to_pdf_from_fitz(txt_path: str, pdf_path: str):
    """Конвертация TXT->PDF через PyMuPDF (если установлен).

    Важно: этот метод использует внешнюю библиотеку. Если ее нет — сгенерируем
    PDF не сможем.
    """
    import fitz  # type: ignore

    doc = fitz.open()
    # создаем документ напрямую
    pdf = fitz.open()
    page = pdf.new_page(width=595, height=842)  # A4-ish

    with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    # Упрощенный вывод: моноширинный текст с переносом
    max_chars = 95
    lines = []
    for paragraph in raw.splitlines():
        if not paragraph.strip():
            lines.append("")
        else:
            lines.extend(_wrap_text(paragraph, max_chars=max_chars))

    x, y = 30, 800
    line_height = 12

    for line in lines:
        if y - line_height < 30:
            page = pdf.new_page(width=595, height=842)
            y = 800
        page.insert_text((x, y), line, fontsize=9, fontname="courier")
        y -= line_height

    pdf.save(pdf_path)
    pdf.close()


def try_convert_text_to_pdf(txt_path: str, pdf_path: str) -> bool:
    """Пытается конвертировать TXT в PDF.

    На текущей среде может не быть зависимости — тогда вернется False.
    """
    try:
        text_to_pdf_from_fitz(txt_path, pdf_path)
        return True
    except Exception:
        return False


def ensure_pdf(txt_path: str, pdf_path: str) -> None:
    ok = try_convert_text_to_pdf(txt_path, pdf_path)
    if not ok:
        raise RuntimeError(
            "Не удалось конвертировать TXT в PDF. "+
            "На системе не найдены зависимости для конвертации (ожидается PyMuPDF 'fitz')."
        )

