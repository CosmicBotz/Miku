#!/usr/bin/env python3
"""Command-line entry point for the Anime Mod Bot.

Usage:
    python run.py                       # uses ./config.yaml
    python run.py --config prod.yaml    # use a different config file
"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Anime-themed Telegram group management bot")
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="Path to the config YAML file (default: config.yaml)"
    )
    args = parser.parse_args()

    from bot.config import load_config
    from bot.logger import setup_logging

    try:
        cfg = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(cfg.log_level)

    from bot.app import run

    run()


if __name__ == "__main__":
    main()
