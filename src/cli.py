"""Консольная точка входа минимального прототипа."""

import argparse
import sys

from src.config import ConfigError, load_settings
from src.graph import GraphBuilder
from src.models import Package, RepositoryError
from src.repository import make_repository
from src.visualization import RenderError, save_visualization


def main(argv=None):
    """Построить граф и сохранить Mermaid с PNG."""
    parser = argparse.ArgumentParser(description="Граф зависимостей NuGet")
    parser.add_argument("config", help="путь к TOML-конфигурации")
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.config)
        repository = make_repository(settings)
        package = Package(settings.package, settings.version)
        graph = GraphBuilder(repository, settings.filter).build(package)
        source, output = save_visualization(graph, settings.output)
    except (ConfigError, RepositoryError, RenderError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Mermaid: {source}")
    print(f"PNG: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
