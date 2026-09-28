"""Консольная точка входа минимального прототипа."""

import argparse
import sys

from src.config import ConfigError, load_settings
from src.graph import GraphBuilder, print_graph
from src.models import Package, RepositoryError
from src.ordering import print_load_order
from src.repository import make_repository


def main(argv=None):
    """Построить и показать полный граф зависимостей."""
    parser = argparse.ArgumentParser(description="Граф зависимостей NuGet")
    parser.add_argument("config", help="путь к TOML-конфигурации")
    parser.add_argument("--load-order", action="store_true",
                        help="порядок загрузки (этап 4)")
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.config)
        repository = make_repository(settings)
        package = Package(settings.package, settings.version)
        graph = GraphBuilder(repository, settings.filter).build(package)
        if args.load_order:
            print_load_order(graph)
        else:
            print_graph(graph)
    except (ConfigError, RepositoryError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
