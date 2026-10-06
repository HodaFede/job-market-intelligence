"""Interface en ligne de commande : `python -m jmi <commande>`."""
from __future__ import annotations

import argparse
import logging

from jmi.config import load_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jmi", description="Job Market Intelligence — pipeline Data / IA")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_collect = sub.add_parser("collect", help="collecte réelle (APIs + scraping)")
    p_collect.add_argument("--source", action="append", choices=["france_travail", "adzuna", "jsonld"],
                           help="limiter à une ou plusieurs sources (répétable)")
    p_demo = sub.add_parser("demo", help="génère le jeu de démonstration synthétique")
    p_demo.add_argument("-n", type=int, default=1200)
    p_demo.add_argument("--seed", type=int, default=42)
    p_run = sub.add_parser("run", help="nettoyage + NLP + SQLite + exports Tableau + rapport")
    p_run.add_argument("--data-mode", choices=["auto", "real", "all"], help="surcharge clean.data_mode")
    sub.add_parser("all", help="collect puis run")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s — %(message)s", datefmt="%H:%M:%S")

    overrides = {"clean": {"data_mode": args.data_mode}} if getattr(args, "data_mode", None) else None
    settings = load_settings(overrides=overrides)

    if args.command in ("collect", "all"):
        from jmi.collect import run_collection
        run_collection(settings, getattr(args, "source", None))
    if args.command == "demo":
        from jmi.collect import write_demo
        path = write_demo(settings, n=args.n, seed=args.seed)
        print(f"Jeu de démonstration écrit : {path}")
    if args.command in ("run", "all"):
        from jmi.pipeline import run_pipeline
        s = run_pipeline(settings)
        print(f"\n✔ {s.n_offers} offres ({s.dataset_label}) — exports dans {settings.path('exports')}")
    return 0
