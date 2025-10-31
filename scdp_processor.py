import re
import pdfplumber

def parse_brazilian_currency(value_str):
    if not value_str:
        return None
    cleaned_value = value_str.replace(".", "").replace(",", ".")
    try:
        return float(cleaned_value)
    except ValueError:
        return None

def process_scdp_line(line, dados):
    bilhete_match = re.search(r"(\d{3}-\d{6,10}|\b\d{10,}\b)", line)
    if not bilhete_match:
        return
    bilhete = bilhete_match.group(1).replace("-", "")
    valores = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", line)
    if valores:
        valor = parse_brazilian_currency(valores[-1])
        if valor:
            dados[bilhete] = valor

def processar_scdp(pdf_path):
    dados = {}
    with pdfplumber.open(pdf_path) as pdf:
        all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    blocos = re.split(r"(?=\d{3}-\d{6,10}|\b\d{10,}\b)", all_text)
    for bloco in blocos:
        process_scdp_line(bloco, dados)
    return dados
