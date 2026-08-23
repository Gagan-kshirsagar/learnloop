from pathlib import Path

from tools.check_boundaries import check_file


def test_allowed_import(tmp_path: Path) -> None:
    app_root = tmp_path / "app"
    learning_dir = app_root / "modules" / "learning"
    learning_dir.mkdir(parents=True)
    f = learning_dir / "service.py"
    f.write_text("from app.modules.identity.api import get_user\n")

    violations = check_file(f, app_root)
    assert len(violations) == 0


def test_disallowed_cross_module_internal_import(tmp_path: Path) -> None:
    app_root = tmp_path / "app"
    learning_dir = app_root / "modules" / "learning"
    learning_dir.mkdir(parents=True)
    f = learning_dir / "service.py"
    f.write_text("from app.modules.identity.internal.repo import UserRepository\n")

    violations = check_file(f, app_root)
    assert len(violations) == 1
    assert "Illegal internal import" in violations[0].message


def test_intra_module_internal_import_allowed(tmp_path: Path) -> None:
    app_root = tmp_path / "app"
    identity_dir = app_root / "modules" / "identity"
    identity_dir.mkdir(parents=True)
    f = identity_dir / "api.py"
    f.write_text("from app.modules.identity.internal.service import IdentityService\n")

    violations = check_file(f, app_root)
    assert len(violations) == 0


def test_shared_cannot_import_modules(tmp_path: Path) -> None:
    app_root = tmp_path / "app"
    shared_dir = app_root / "shared"
    shared_dir.mkdir(parents=True)
    f = shared_dir / "db.py"
    f.write_text("from app.modules.catalog.api import CatalogService\n")

    violations = check_file(f, app_root)
    assert len(violations) == 1
    assert "shared/ cannot import from modules" in violations[0].message
