from __future__ import annotations

import json
import re
import time
from pathlib import Path

from deep_translator import GoogleTranslator


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "article" / "TCC_Evasao.tex"
DST = ROOT / "article" / "TCC_Evasao_en.tex"
CACHE_PATH = ROOT / "tmp" / "article_translate_cache_en.json"

TRANSLATOR = GoogleTranslator(source="pt", target="en")

SECTION_COMMANDS = {
    "chapter",
    "section",
    "subsection",
    "subsubsection",
    "paragraph",
    "titulo",
    "local",
    "instituicao",
    "tipotrabalho",
    "preambulo",
    "orientador",
    "caption",
    "figsource",
    "tablesource",
    "tablenote",
}

NON_TRANSLATABLE_PATTERNS = [
    r"\\textcite\{[^{}]*\}",
    r"\\parencite\{[^{}]*\}",
    r"\\citeyear\{[^{}]*\}",
    r"\\cite[p|t]?\*?(?:\[[^\]]*\])?\{[^{}]*\}",
    r"\\ref\{[^{}]*\}",
    r"\\label\{[^{}]*\}",
    r"\\url\{[^{}]*\}",
    r"\\autoref\{[^{}]*\}",
    r"\\eqref\{[^{}]*\}",
    r"\\includegraphics(?:\[[^\]]*\])?\{[^{}]*\}",
    r"\\begin\{[^{}]*\}",
    r"\\end\{[^{}]*\}",
    r"\\item(?:\[[^\]]*\])?",
    r"\\[A-Za-z]+(?:\[[^\]]*\])?\{[^{}]*\}",
    r"\\[A-Za-z]+",
    r"\$[^$]*\$",
]


def load_cache() -> dict[str, str]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def protect(text: str) -> tuple[str, dict[str, str]]:
    mapping: dict[str, str] = {}
    protected = text
    counter = 0

    for pattern in NON_TRANSLATABLE_PATTERNS:
        while True:
            match = re.search(pattern, protected)
            if not match:
                break
            token = f"ZXTOKEN{counter}ZX"
            mapping[token] = match.group(0)
            protected = protected[: match.start()] + token + protected[match.end() :]
            counter += 1

    return protected, mapping


def restore(text: str, mapping: dict[str, str]) -> str:
    restored = text
    for _ in range(10):
        changed = False
        for token, original in mapping.items():
            if token in restored:
                restored = restored.replace(token, original)
                changed = True
        if not changed:
            break
    return restored


def needs_translation(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return bool(re.search(r"[A-Za-zÀ-ÿ]", stripped))


class SegmentRegistry:
    def __init__(self) -> None:
        self.items: list[tuple[str, str, dict[str, str]]] = []

    def add(self, text: str) -> str:
        if not needs_translation(text):
            return text
        protected, mapping = protect(text)
        token = f"@@TR{len(self.items)}@@"
        self.items.append((token, protected, mapping))
        return token


def translate_command_line(line: str, registry: SegmentRegistry) -> str:
    stripped = line.rstrip("\n")
    m = re.match(r"^(\s*)\\([A-Za-z]+)(\*?)(\[[^\]]*\])?\{(.*)\}$", stripped)
    if not m:
        return line

    indent, cmd, star, opt, content = m.groups()
    if cmd not in SECTION_COMMANDS:
        return line

    opt = opt or ""
    return f"{indent}\\{cmd}{star}{opt}{{{registry.add(content)}}}\n"


def translate_paragraph_label_line(line: str, registry: SegmentRegistry) -> str:
    stripped = line.rstrip("\n")
    m = re.match(r"^(\s*\\paragraph\*\{)([^}]*)\}(.*)$", stripped)
    if not m:
        return line

    start, label, rest = m.groups()
    label_token = registry.add(label)
    rest_token = registry.add(rest) if needs_translation(rest) else rest
    return f"{start}{label_token}}}{rest_token}\n"


def translate_item_line(line: str, registry: SegmentRegistry) -> str:
    stripped = line.rstrip("\n")
    m = re.match(r"^(\s*\\item(?:\[[^\]]*\])?\s+)(.*)$", stripped)
    if not m:
        return line

    prefix, content = m.groups()
    return prefix + registry.add(content) + "\n"


def translate_table_row(line: str, registry: SegmentRegistry) -> str:
    stripped = line.rstrip("\n")
    if "&" not in stripped or not stripped.strip().endswith(r"\\"):
        return line

    lead = re.match(r"^\s*", stripped).group(0)
    body = stripped[len(lead) :]
    body = body[:-2].rstrip()
    cells = [cell.strip() for cell in body.split("&")]

    translated_cells: list[str] = []
    for cell in cells:
        if not needs_translation(cell) or re.fullmatch(r"[\d\s,.;:+\-()/%$\\]+", cell):
            translated_cells.append(cell)
        else:
            translated_cells.append(registry.add(cell))

    return f"{lead}{' & '.join(translated_cells)} \\\\\n"


def translate_addcontentsline(line: str, registry: SegmentRegistry) -> str:
    stripped = line.rstrip("\n")
    m = re.match(r"^(\s*\\addcontentsline\{[^{}]*\}\{[^{}]*\}\{)(.*)(\})$", stripped)
    if not m:
        return line
    start, content, end = m.groups()
    return f"{start}{registry.add(content)}{end}\n"


def translate_plain_line(line: str, registry: SegmentRegistry) -> str:
    stripped = line.rstrip("\n")
    if not stripped.strip():
        return line
    if stripped.lstrip().startswith("%"):
        return line
    if re.match(r"^\s*\\(textcite|parencite|citeyear|textit|textbf|footnote|hyperref)", stripped):
        return registry.add(stripped) + "\n"
    if stripped.lstrip().startswith("\\"):
        return line
    return registry.add(stripped) + "\n"


def batch_translate_unique(cache: dict[str, str], registry: SegmentRegistry) -> None:
    pending: list[str] = []
    seen: set[str] = set()

    for _, protected, _ in registry.items:
        if protected in cache or protected in seen:
            continue
        seen.add(protected)
        if not needs_translation(protected):
            cache[protected] = protected
        else:
            pending.append(protected)

    for i in range(0, len(pending), 25):
        chunk = pending[i : i + 25]
        translated_chunk: list[str] | None = None
        for attempt in range(4):
            try:
                translated_chunk = TRANSLATOR.translate_batch(chunk)
                break
            except Exception:
                time.sleep(2 * (attempt + 1))

        if translated_chunk is None:
            for item in chunk:
                cache[item] = item
        else:
            for original, translated in zip(chunk, translated_chunk):
                cache[original] = translated or original

        save_cache(cache)
        print(f"Translated {min(i + len(chunk), len(pending))}/{len(pending)} segments")


def replace_tokens(text: str, cache: dict[str, str], registry: SegmentRegistry) -> str:
    output = text
    for _ in range(20):
        changed = False
        for token, protected, mapping in registry.items:
            translated = cache.get(protected, protected)
            restored = restore(translated, mapping)
            if token in output:
                output = output.replace(token, restored)
                changed = True
        if not changed:
            break
    return output


def post_process(text: str) -> str:
    text = text.replace(r"\usepackage[brazil]{babel}", r"\usepackage[english]{babel}")
    text = text.replace(
        r"\usepackage[style=abnt,backend=biber,language=brazil]{biblatex}",
        r"\usepackage[style=abnt,backend=biber,language=english]{biblatex}",
    )
    text = text.replace(
        r"\newcommand{\tablesource}[1]{{\raggedright \fontsize{10}{12}\selectfont \textit{Fonte: #1}\par}}",
        r"\newcommand{\tablesource}[1]{{\raggedright \fontsize{10}{12}\selectfont \textit{Source: #1}\par}}",
    )
    text = text.replace(
        r"\newcommand{\figsource}[1]{{\raggedright \fontsize{10}{12}\selectfont \textit{Fonte: #1}\par}}",
        r"\newcommand{\figsource}[1]{{\raggedright \fontsize{10}{12}\selectfont \textit{Source: #1}\par}}",
    )
    text = text.replace(r"\renewcommand{\resumoname}{Resumo}", r"\renewcommand{\resumoname}{Abstract}")
    text = text.replace(r"\renewcommand{\abstractname}{Abstract}", r"\renewcommand{\abstractname}{Abstract}")
    text = text.replace(r"\tableofcontents*", r"\renewcommand{\contentsname}{Contents}" + "\n" + r"\tableofcontents*")

    text = text.replace("Images/artigo/", "Images/artigo_en/")
    text = text.replace("Images/plotly/", "Images/plotly_en/")
    text = text.replace("{Images/roc_teste_p1.png}", "{Images/roc_teste_p1_en.png}")
    text = text.replace("{Images/roc_teste_p2.png}", "{Images/roc_teste_p2_en.png}")
    text = text.replace("{Images/roc_teste_p4.png}", "{Images/roc_teste_p4_en.png}")

    start = text.find(r"% Abstract em inglês")
    if start != -1:
        end = text.find(r"\cleardoublepage", start)
        if end != -1:
            text = text[:start] + r"\cleardoublepage" + text[end + len(r"\cleardoublepage") :]

    front_replacements = {
        r"\titulo{": r"\titulo{",
        "Modelagem Preditiva da Evasão Acadêmica com Aprendizado de Máquina": "Predictive Modeling of Academic Dropout with Machine Learning",
        "Universidade Federal de Uberlândia": "Federal University of Uberlandia",
        "Faculdade de Gestão e Negócios": "School of Management and Business",
        "Curso de Gestão da Informação": "Information Management Program",
        "Trabalho de Conclusão de Curso": "Undergraduate Thesis",
        "Trabalho apresentado ao curso de Gestão da Informação da Universidade Federal de Uberlândia como requisito parcial para a obtenção do grau de Bacharel.": "Thesis submitted to the Information Management Program at the Federal University of Uberlandia in partial fulfillment of the requirements for the Bachelor’s degree.",
        "Profª. Drª": "Prof. Dr.",
        r"\local{Uberlândia -- MG}": r"\local{Uberlandia, Brazil}",
        r"\noindent\textbf{Palavras-chave:}": r"\noindent\textbf{Keywords:}",
        "Apêndice A -- Variáveis preditoras utilizadas nos modelos": "Appendix A -- Predictor variables used in the models",
    }
    for old, new in front_replacements.items():
        text = text.replace(old, new)

    return text


def main() -> None:
    source = SRC.read_text(encoding="utf-8")
    registry = SegmentRegistry()
    out_lines: list[str] = []

    for line in source.splitlines(keepends=True):
        translated = line
        translated = translate_command_line(translated, registry)
        translated = translate_paragraph_label_line(translated, registry)
        translated = translate_item_line(translated, registry)
        translated = translate_table_row(translated, registry)
        translated = translate_addcontentsline(translated, registry)
        translated = translate_plain_line(translated, registry)
        out_lines.append(translated)

    intermediate = "".join(out_lines)
    cache = load_cache()
    batch_translate_unique(cache, registry)
    translated = replace_tokens(intermediate, cache, registry)
    translated = post_process(translated)
    DST.write_text(translated, encoding="utf-8")
    print(f"Written {DST}")


if __name__ == "__main__":
    main()
