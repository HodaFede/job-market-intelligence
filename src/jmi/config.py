"""Chargement de la configuration et résolution des chemins du projet."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv(root: Path) -> None:
    """Charge `.env` si python-dotenv est disponible (optionnel)."""
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover
        return
    env_file = root / ".env"
    if env_file.exists():
        load_dotenv(env_file)


@dataclass
class Settings:
    root: Path
    raw: dict[str, Any]

    def path(self, key: str) -> Path:
        return self.root / self.raw["paths"][key]

    def section(self, name: str) -> dict[str, Any]:
        return self.raw.get(name, {})

    @property
    def keywords(self) -> list[str]:
        return list(self.raw.get("keywords", []))


def load_settings(root: Path | str | None = None, overrides: dict[str, Any] | None = None) -> Settings:
    root = Path(root or os.environ.get("JMI_ROOT") or DEFAULT_ROOT).resolve()
    _load_dotenv(root)
    cfg_file = root / "config" / "settings.yaml"
    if not cfg_file.exists():  # ex. tests dans un dossier temporaire
        cfg_file = DEFAULT_ROOT / "config" / "settings.yaml"
    with open(cfg_file, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    for key, value in (overrides or {}).items():
        if isinstance(value, dict) and isinstance(raw.get(key), dict):
            raw[key].update(value)
        else:
            raw[key] = value
    return Settings(root=root, raw=raw)


def resource(rel_path: str, settings: Settings | None = None) -> Path:
    """Fichier de référence (config/, sql/) : cherché dans la racine, sinon dans le dépôt."""
    if settings is not None:
        candidate = settings.root / rel_path
        if candidate.exists():
            return candidate
    return DEFAULT_ROOT / rel_path
