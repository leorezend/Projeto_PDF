import pdfplumber
import re

def parse_valor_str_to_float(v):
    if not v:
        return 0.0
    return float(v.replace('.', '').replace(',', '.'))

AGG_TOTAL_PATTERNS = [
    r"Total do Centro", r"Total do Centro de Custo", r"Totais da Passagem",
    r"Total\s+do\s+Centro", r"Total\s+da\s+Passagem", r"Total geral",
    r"Total\s+geral", r"Total\s+do\s+Centro:", r"Totais",
    r"Total\s+do\s+Centro\s+de\s+Custo"
]

def is_agg_line(line):
    for pat in AGG_TOTAL_PATTERNS:
        if re.search(pat, line, re.IGNORECASE):
            return True
    return False


def process_block_and_extract(block_text):
    lines = [l.rstrip() for l in block_text.splitlines() if l.strip()]
    cleaned_lines = []
    for ln in lines:
        if is_agg_line(ln):
            break
        cleaned_lines.append(ln)

    cleaned_block = "\n".join(cleaned_lines)
    bilhete_m = re.search(r"Bilhete:\s*(\d{10,})", cleaned_block)
    bilhete = bilhete_m.group(1) if bilhete_m else None

    valores_por_linha = []
    for ln in cleaned_lines:
        vals = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", ln)
        valores_por_linha.append((ln, vals))

    tarifa = fee = taxas = total = None
    if bilhete:
        for ln, vals in valores_por_linha:
            if bilhete in ln:
                if len(vals) >= 4:
                    tarifa, fee, taxas, total = vals[-4:]
                elif len(vals) == 3:
                    tarifa, taxas, total = vals[-3:]
                    fee = "0,00"
                elif len(vals) == 2:
                    tarifa, total = vals[-2:]
                    fee = "0,00"
                elif len(vals) == 1:
                    total = vals[-1]
                break

    if total is None:
        vals_block = []
        for _, vals in valores_por_linha:
            vals_block.extend(vals)
        if len(vals_block) >= 4:
            tarifa, fee, taxas, total = vals_block[-4:]
        elif len(vals_block) == 3:
            tarifa, taxas, total = vals_block[-3:]
            fee = "0,00"
        elif len(vals_block) == 2:
            tarifa, total = vals_block[-2:]
            fee = "0,00"
        elif len(vals_block) == 1:
            total = vals_block[-1]

    tarifa_f = parse_valor_str_to_float(tarifa or "0,00")
    fee_f = parse_valor_str_to_float(fee or "0,00")
    taxas_f = parse_valor_str_to_float(taxas or "0,00")
    total_f = parse_valor_str_to_float(total or "0,00")

    ok = abs((tarifa_f + fee_f + taxas_f) - total_f) < 1.0

    return {
        "Bilhete": bilhete,
        "Tarifa": tarifa_f,
        "Fee": fee_f,
        "Taxas": taxas_f,
        "Total": total_f,
        "Consistente": ok
    }


def processar_voetuor(pdf_path):
    registros = []
    current_block_lines = []
    current_seq = None
    seq_pattern = re.compile(r"^(\d{1,3})\s")

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = text.splitlines()
            for line in lines:
                line_strip = line.strip()
                if not line_strip:
                    continue
                m = seq_pattern.match(line_strip)
                if m:
                    seq = int(m.group(1))
                    if current_block_lines:
                        block_text = "\n".join(current_block_lines)
                        result = process_block_and_extract(block_text)
                        if result["Bilhete"]:
                            registros.append({"Seq": current_seq, **result})
                        current_block_lines = []
                    current_seq = seq
                current_block_lines.append(line_strip)

        if current_block_lines and current_seq is not None:
            block_text = "\n".join(current_block_lines)
            result = process_block_and_extract(block_text)
            if result["Bilhete"]:
                registros.append({"Seq": current_seq, **result})

    return registros
