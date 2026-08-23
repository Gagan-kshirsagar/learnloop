"""
CI check: enforces modular monolith boundaries in apps/api/app.

Rules:
1. Each module under app/modules/<name>/ exposes ONE public surface: api.py.
   Nothing outside a module may import its internal/ package.
2. app/shared/ is cross-cutting infra and must NOT import from app/modules/.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    file_path: Path
    line: int
    message: str


def get_module_name(file_path: Path, app_root: Path) -> str | None:
    try:
        rel_path = file_path.relative_to(app_root)
    except ValueError:
        return None
    parts = rel_path.parts
    if len(parts) >= 2 and parts[0] == "modules":
        return parts[1]
    return None


def is_shared(file_path: Path, app_root: Path) -> bool:
    try:
        rel_path = file_path.relative_to(app_root)
    except ValueError:
        return False
    return len(rel_path.parts) >= 1 and rel_path.parts[0] == "shared"


def check_file(file_path: Path, app_root: Path) -> list[Violation]:
    violations: list[Violation] = []
    current_module = get_module_name(file_path, app_root)
    in_shared = is_shared(file_path, app_root)

    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except SyntaxError as e:
        violations.append(Violation(file_path, e.lineno or 1, f"Syntax error: {e.msg}"))
        return violations

    for node in ast.walk(tree):
        imported_names: list[tuple[str, int]] = []

        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            if module_name:
                imported_names.append((module_name, node.lineno))

        for full_import, lineno in imported_names:
            # Rule 2: shared cannot import from modules
            if in_shared and full_import.startswith("app.modules"):
                violations.append(
                    Violation(
                        file_path,
                        lineno,
                        f"shared/ cannot import from modules: '{full_import}'",
                    )
                )

            # Rule 1: No cross-module internal imports
            if "app.modules." in full_import:
                parts = full_import.split(".")
                try:
                    idx = parts.index("modules")
                    if len(parts) > idx + 2:
                        target_mod = parts[idx + 1]
                        sub_pkg = parts[idx + 2]
                        if sub_pkg == "internal" and target_mod != current_module:
                            violations.append(
                                Violation(
                                    file_path,
                                    lineno,
                                    f"Illegal internal import in module '{target_mod}': "
                                    f"'{full_import}'. Import from "
                                    f"'app.modules.{target_mod}.api' instead.",
                                )
                            )
                except ValueError:
                    pass

    return violations


def main() -> int:
    base_dir = Path(__file__).resolve().parent.parent
    app_root = base_dir / "app"
    if not app_root.exists():
        # Maybe invoked from repo root
        app_root = Path.cwd() / "apps" / "api" / "app"
        if not app_root.exists():
            app_root = Path.cwd() / "app"

    if not app_root.exists():
        print(f"Error: Could not locate app/ directory starting from {base_dir}")
        return 1

    py_files = sorted(app_root.rglob("*.py"))
    all_violations: list[Violation] = []

    for file_path in py_files:
        violations = check_file(file_path, app_root)
        all_violations.extend(violations)

    if all_violations:
        print(f"❌ Module boundary check failed with {len(all_violations)} violation(s):\n")
        for v in all_violations:
            try:
                rel = v.file_path.relative_to(app_root.parent)
            except ValueError:
                rel = v.file_path
            print(f"  {rel}:{v.line} -> {v.message}")
        print("\nFix these violations to maintain modular isolation.")
        return 1

    print(f"✅ Module boundary check passed ({len(py_files)} files checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
