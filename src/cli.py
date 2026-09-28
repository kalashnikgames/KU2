"""Консольная точка входа минимального прототипа."""

import argparse
import sys
from dataclasses import asdict

from src.config import ConfigError, load_settings


def main(argv=None):
    """Загрузить конфигурацию и вывести пары ключ-значение."""
    parser = argparse.ArgumentParser(description="Граф зависимостей NuGet")
    parser.add_argument("config", help="путь к TOML-конфигурации")
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.config)
    except ConfigError as error:
        print(error, file=sys.stderr)
        return 1
    for key, value in asdict(settings).items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
