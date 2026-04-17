from __future__ import annotations

import argparse
import sys

from mlx_yap import config as cfg_mod


def cmd_start(_args: argparse.Namespace) -> None:
    from mlx_yap.daemon import Daemon
    Daemon().run()


def cmd_mode(args: argparse.Namespace) -> None:
    cfg = cfg_mod.load()
    caps = cfg.get("capabilities", {})
    name = args.name
    if name not in caps:
        print(f"yap: unknown capability '{name}'. Available: {', '.join(caps)}", file=sys.stderr)
        sys.exit(1)
    cfg_mod.update_field("active_capability", name)
    cap = caps.get(name)
    desc = cap["description"] if cap else "no post-processing"
    print(f"Mode set to '{name}' — {desc}")


def cmd_context(args: argparse.Namespace) -> None:
    if args.project is not None:
        cfg_mod.update_field("context.project_name", args.project)
        print(f"Context updated: project_name = '{args.project}'")
    else:
        cfg = cfg_mod.load()
        ctx = cfg.get("context", {})
        for k, v in ctx.items():
            print(f"  {k}: {v!r}")


def cmd_language(args: argparse.Namespace) -> None:
    if args.code is not None:
        code = args.code.lower()
        cfg_mod.update_field("whisper.language", code)
        print(f"Language set to '{code}'")
    else:
        cfg = cfg_mod.load()
        lang = cfg["whisper"].get("language")
        if lang:
            print(f"Current language: {lang}")
        else:
            print("Current language: auto-detect")


def cmd_capabilities(_args: argparse.Namespace) -> None:
    cfg = cfg_mod.load()
    active = cfg.get("active_capability", "raw")
    caps = cfg.get("capabilities", {})
    for name, cap in caps.items():
        marker = " *" if name == active else "  "
        if cap is None:
            desc = "no post-processing"
        else:
            desc = cap.get("description", "")
        print(f"{marker} {name}: {desc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="yap",
        description="mlx-yap — local voice dictation for macOS (MLX-powered)",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("start", help="Start the daemon (default)")

    mode_p = sub.add_parser("mode", help="Set active capability")
    mode_p.add_argument("name", help="Capability name (e.g. raw, cleanup, summarize, clarify)")

    ctx_p = sub.add_parser("context", help="Update context fields")
    ctx_p.add_argument("--project", metavar="NAME", help="Set project name")

    lang_p = sub.add_parser("language", help="View or set transcription language")
    lang_p.add_argument("code", nargs="?", default=None, help="Language code (e.g. en, fr, de, ja) or name (e.g. english, french)")

    sub.add_parser("capabilities", help="List available capabilities")

    args = parser.parse_args()

    if args.command is None or args.command == "start":
        cmd_start(args)
    elif args.command == "mode":
        cmd_mode(args)
    elif args.command == "context":
        cmd_context(args)
    elif args.command == "language":
        cmd_language(args)
    elif args.command == "capabilities":
        cmd_capabilities(args)
    else:
        parser.print_help()
        sys.exit(1)
