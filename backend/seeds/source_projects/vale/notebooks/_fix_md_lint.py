"""Fix MD022 (blanks around headings) e MD031 (blanks around fences) nos
arquivos markdown da raiz e docs/.

Mecanico e seguro: nao altera conteudo, apenas insere linhas em branco
antes/depois quando faltam.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "MEMORY.md",
    ROOT / "docs" / "decisions.md",
    ROOT / "docs" / "hypotheses.md",
    ROOT / "docs" / "audit_fase2.md",
]

HEADING = re.compile(r"^#{1,6}\s")
FENCE = re.compile(r"^```")


def fix(text: str) -> tuple[str, int, int]:
    lines = text.split("\n")
    out: list[str] = []
    fixed_md022 = 0
    fixed_md031 = 0
    in_fence = False

    for i, line in enumerate(lines):
        is_heading = HEADING.match(line) is not None
        is_fence = FENCE.match(line) is not None

        # MD022: heading deve ter blank antes (a menos que seja a primeira linha
        # ou ja seja precedida por blank).
        if is_heading and out and out[-1].strip() != "":
            out.append("")
            fixed_md022 += 1

        # MD031: fence opening deve ter blank antes.
        # MD031: fence closing deve ter blank depois.
        if is_fence and not in_fence and out and out[-1].strip() != "":
            out.append("")
            fixed_md031 += 1

        out.append(line)

        if is_fence:
            in_fence = not in_fence

        # MD022: heading deve ter blank depois.
        if is_heading and i + 1 < len(lines) and lines[i + 1].strip() != "":
            out.append("")
            fixed_md022 += 1

    return "\n".join(out), fixed_md022, fixed_md031


def main() -> None:
    for p in TARGETS:
        text = p.read_text(encoding="utf-8", errors="replace")
        new_text, m22, m31 = fix(text)
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            print(f"  {p.name}: MD022={m22} MD031={m31}  (escrito)")
        else:
            print(f"  {p.name}: ja limpo")


if __name__ == "__main__":
    main()
