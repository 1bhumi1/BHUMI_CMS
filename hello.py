from pathlib import Path

EXCLUDE = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    "graphify-out",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "node_modules",
    "logs",
    "uploads",
}

def print_tree(path: Path, prefix=""):
    items = sorted(
        [p for p in path.iterdir() if p.name not in EXCLUDE],
        key=lambda x: (x.is_file(), x.name.lower())
    )

    for i, item in enumerate(items):
        connector = "└── " if i == len(items) - 1 else "├── "
        print(prefix + connector + item.name)

        if item.is_dir():
            extension = "    " if i == len(items) - 1 else "│   "
            print_tree(item, prefix + extension)

root = Path(".")
print(root.resolve().name)
print_tree(root)