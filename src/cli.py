"""Консольная точка входа минимального прототипа."""

import argparse
import sys

from src.config import ConfigError, load_settings
from src.models import Package, RepositoryError
from src.repository import make_repository


def main(argv=None):
    """Прочитать настройки и вывести прямые зависимости пакета."""
    parser = argparse.ArgumentParser(description="Граф зависимостей NuGet")
    parser.add_argument("config", help="путь к TOML-конфигурации")
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.config)
        repository = make_repository(settings)
        package = Package(settings.package, settings.version)
        dependencies = repository.direct(package)
    except (ConfigError, RepositoryError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Прямые зависимости {package.label} ({settings.framework}):")
    for dependency in dependencies:
        print(f"{dependency.name} {dependency.constraint}")
    if not dependencies:
        print("(нет)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
