"""Remove travessoes (em-dashes) no artigo LaTeX fora da secao Referencial Teorico.

- Linhas 124..387 (Referencial Teorico): NAO processa.
- Demais linhas: substitui " --- " por ", " e " ---," por ","
- Em captions, o primeiro " --- " vira ":" para manter a leitura.
"""
from pathlib import Path
import sys

REFER_START = 124
REFER_END = 387


def process_line(line: str) -> str:
    if "\\caption{" in line and " --- " in line:
        parts = line.split(" --- ")
        if len(parts) > 1:
            line = parts[0] + ": " + ", ".join(parts[1:])

    line = line.replace(" ---,", ",")
    line = line.replace(" --- ", ", ")
    return line


def process_file(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = 0
    for i, line in enumerate(lines):
        line_no = i + 1
        if REFER_START <= line_no <= REFER_END:
            continue
        if "---" in line:
            new_line = process_line(line)
            if new_line != line:
                lines[i] = new_line
                changed += 1
    path.write_text("".join(lines), encoding="utf-8")
    print(f"Processado: {path}  ({changed} linhas alteradas)")


if __name__ == "__main__":
    targets = [
        Path(r"D:\TCC - versão final\article\TCC_Evasao.tex"),
        Path(r"D:\TCC - Diego Xavier\06_artefatos_finais\01_artigo\TCC_Evasao.tex"),
    ]
    for t in targets:
        if not t.exists():
            print(f"ERRO: nao existe {t}", file=sys.stderr)
            continue
        process_file(t)
    print("Feito.")
