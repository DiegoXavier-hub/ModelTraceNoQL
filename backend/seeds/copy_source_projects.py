"""Copy lightweight metadata from the user's local source projects.

We never touch the original folders. We make read-only-style copies of
small text files (READMEs, requirements, manifests, top-level src files)
into `backend/seeds/source_projects/<slug>/` so the seed generator and any
auditor can verify the provenance of each project registered in the DB.

Large binaries, datasets, model artifacts, .venv, node_modules and PDFs
are intentionally skipped. The goal is provenance, not data replay.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEST_ROOT = REPO_ROOT / "backend" / "seeds" / "source_projects"

# File extensions that are safe to copy (small, textual, metadata-only)
TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".ini",
    ".rst",
    ".gitignore",
    ".ipynb",
}

# Per-file size cap. Anything larger is skipped (avoids accidental copy
# of a giant txt log or vendored CSV).
MAX_FILE_BYTES = 256 * 1024  # 256 KB

# Directory names that are always skipped (no matter the depth).
SKIPPED_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
    ".claude",
    ".remember",
    ".mempalace",
    "data",            # raw datasets
    "Base de Dados",   # raw datasets (Vale)
    "outputs",         # generated outputs
    "reports",         # generated reports
    "tmp",
    "figures",         # generated figures
    "tables",          # generated tables
    "portfolio",
    ".pytest_cache",
}


@dataclass
class SourceProject:
    slug: str
    label: str
    source_path: Path
    description: str
    extra_subdirs: list[str] = field(default_factory=list)


SOURCES: list[SourceProject] = [
    SourceProject(
        slug="vale",
        label="Vale - Industrial Predictive Maintenance",
        source_path=Path(r"C:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Vale"),
        description="Modelos industriais para antecipar eventos DontGo em equipamentos de mina.",
        extra_subdirs=["src", "docs", "notebooks", "papers"],
    ),
    SourceProject(
        slug="cnpj-survival",
        label="CNPJ Closure Risk Radar",
        source_path=Path(
            r"C:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\Análise de Sobrevivência de Empresas Brasileiras Quanto Tempo Dura um CNPJ\analise-sobrevivencia-cnpj"
        ),
        description="Análise de sobrevivência aplicada a CNPJs ativos no Brasil.",
        extra_subdirs=["src", "artigo"],
    ),
    SourceProject(
        slug="llms-microscope",
        label="LLMs Sob o Microscópio",
        source_path=Path(
            r"C:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\LLMs sob o microscópio\llms-microscopio"
        ),
        description="Avaliação metódica de LLMs em tarefas controladas.",
        extra_subdirs=["src", "artigo"],
    ),
    SourceProject(
        slug="ml-from-scratch",
        label="ML From Scratch - Algorithms Lab",
        source_path=Path(
            r"C:\Users\DiegoHenriqueXavier\Documents\Projetos - Dados\ML from scratch"
        ),
        description="Implementações didáticas dos principais algoritmos de ML.",
        extra_subdirs=[
            "Decision Tree",
            "KMeans",
            "KNN",
            "Linear Regression",
            "Logistic Regression",
            "Naive Bayes",
            "PCA",
            "Perceptron",
            "Random Forest",
            "SVM",
        ],
    ),
    SourceProject(
        slug="tcc-student-outcomes",
        label="TCC Student Outcomes",
        source_path=Path(r"D:\TCC - versão final"),
        description="TCC sobre rastreabilidade de decisões e desfechos estudantis.",
        extra_subdirs=["src", "scripts", "docs", "article"],
    ),
]


def _should_copy_file(file_path: Path) -> bool:
    if file_path.name.startswith("~$"):
        return False
    if file_path.suffix.lower() not in TEXT_EXTENSIONS:
        return False
    try:
        if file_path.stat().st_size > MAX_FILE_BYTES:
            return False
    except OSError:
        return False
    return True


def _copy_tree(source: Path, dest: Path, max_depth: int = 4) -> tuple[int, int]:
    copied = 0
    skipped = 0
    if not source.exists():
        return 0, 0

    base_parts = len(source.parts)
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if any(part in SKIPPED_DIRS for part in relative.parts):
            skipped += 1
            continue
        if len(relative.parts) > max_depth:
            skipped += 1
            continue
        if not _should_copy_file(path):
            skipped += 1
            continue
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(path, target)
            copied += 1
        except (OSError, PermissionError):
            skipped += 1
    return copied, skipped


def copy_all() -> dict[str, dict]:
    """Run the copy and return a manifest with counts per project."""
    DEST_ROOT.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}

    for project in SOURCES:
        dest = DEST_ROOT / project.slug
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        total_copied = 0
        total_skipped = 0

        if not project.source_path.exists():
            manifest[project.slug] = {
                "label": project.label,
                "source": str(project.source_path),
                "status": "source_not_found",
                "copied": 0,
                "skipped": 0,
            }
            continue

        # Top-level files (READMEs, requirements, LICENSE, gitignore...)
        for entry in project.source_path.iterdir():
            if entry.is_file() and _should_copy_file(entry):
                target = dest / entry.name
                try:
                    shutil.copy2(entry, target)
                    total_copied += 1
                except (OSError, PermissionError):
                    total_skipped += 1

        # Allowed subdirectories
        for subdir_name in project.extra_subdirs:
            sub_source = project.source_path / subdir_name
            sub_dest = dest / subdir_name
            copied, skipped = _copy_tree(sub_source, sub_dest)
            total_copied += copied
            total_skipped += skipped

        manifest[project.slug] = {
            "label": project.label,
            "source": str(project.source_path),
            "status": "ok",
            "copied": total_copied,
            "skipped": total_skipped,
            "destination": str(dest),
            "description": project.description,
        }

    return manifest


if __name__ == "__main__":
    manifest = copy_all()
    import json

    print(json.dumps(manifest, indent=2, ensure_ascii=False))
