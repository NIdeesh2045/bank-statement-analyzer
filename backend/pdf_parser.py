import pymupdf


def extract_text_from_pdf(pdf_path):
    document = pymupdf.open(pdf_path)

    all_text = []

    for page in document:
        text = page.get_text()
        all_text.append(text)

    document.close()

    return "\n".join(all_text)