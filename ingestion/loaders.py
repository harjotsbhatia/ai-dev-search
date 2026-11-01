from dataclasses import dataclass, field
from pathlib import Path

EXTENSION_LANGUAGES = {".java": "java", ".py": "python", ".md": "markdown", ".txt": "text"}


@dataclass
class LoadedFile:
    source: str  # top-level folder under data/: docs | incidents | code
    file_path: str  # path relative to data/
    text: str
    metadata: dict = field(default_factory=dict)


def load_files(data_dir: Path) -> list[LoadedFile]:
    files = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix not in EXTENSION_LANGUAGES:
            continue
        rel = path.relative_to(data_dir)
        metadata = {"language": EXTENSION_LANGUAGES[path.suffix]}
        if path.suffix == ".java":
            metadata["class"] = path.stem
        files.append(
            LoadedFile(
                source=rel.parts[0],
                file_path=str(rel),
                text=path.read_text(encoding="utf-8"),
                metadata=metadata,
            )
        )
    return files
