"""HTTP NuGet V3 и файловый тестовый репозиторий."""

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from src.manifest import parse_manifest
from src.models import Dependency, Package, RepositoryError
from src.versions import normalize_version, resolve_version


HTTP_TIMEOUT = 25


def fetch_bytes(url):
    """Прочитать ресурс HTTP стандартной библиотекой Python."""
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as response:
            return response.read()
    except (OSError, urllib.error.URLError) as error:
        raise RepositoryError(f"HTTP {url}: {error}") from error


def fetch_json(url):
    """Прочитать JSON-ресурс и объяснить ошибку формата."""
    try:
        document = json.loads(fetch_bytes(url))
    except (ValueError, UnicodeError) as error:
        raise RepositoryError(f"неверный JSON {url}: {error}") from error
    if not isinstance(document, dict):
        raise RepositoryError(f"JSON {url}: требуется объект")
    return document


class NugetRepository:
    """Самостоятельно получать версии и манифесты из NuGet V3."""

    def __init__(self, url, framework):
        """Найти PackageBaseAddress и подготовить кэш в памяти."""
        self.framework = framework
        self.versions = {}
        self.manifests = {}
        if url.rstrip("/").endswith("index.json"):
            index = fetch_json(url)
            addresses = [
                item["@id"] for item in index.get("resources", [])
                if isinstance(item, dict)
                and "PackageBaseAddress/3.0.0" in item.get("@type", "")
                and isinstance(item.get("@id"), str)
            ]
            if not addresses:
                raise RepositoryError("NuGet V3: no PackageBaseAddress/3.0.0")
            url = addresses[0]
        self.base = url.rstrip("/") + "/"

    def direct(self, package):
        """Получить прямые зависимости строго указанной версии."""
        key = (package.name.lower(), normalize_version(package.version))
        if key not in self.manifests:
            name, version = key
            url = f"{self.base}{name}/{version}/{name}.nuspec"
            data = fetch_bytes(url)
            self.manifests[key] = parse_manifest(data, self.framework)
        return self.manifests[key]

    def resolve(self, name, constraint):
        """Разрешить диапазон по списку версий данного репозитория."""
        key = name.lower()
        if key not in self.versions:
            document = fetch_json(f"{self.base}{key}/index.json")
            self.versions[key] = document.get("versions", [])
        version = resolve_version(self.versions[key], constraint)
        return Package(name, version)


class TestRepository:
    """Граф JSON с именами из больших латинских букв."""

    def __init__(self, path, version):
        """Прочитать и проверить весь тестовый репозиторий."""
        self.version = version
        try:
            graph = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise RepositoryError(f"тестовый репозиторий: {error}") from error
        self.graph = validate_test_graph(graph)

    def direct(self, package):
        """Вернуть зависимости выбранной тестовой вершины."""
        if package.name not in self.graph:
            raise RepositoryError(f"пакет не найден: {package.name}")
        return [Dependency(name, f"[{self.version}]")
                for name in self.graph[package.name]]

    def resolve(self, name, constraint):
        """В тестовом графе все вершины используют заданную версию."""
        return Package(name, self.version)


def validate_test_graph(graph):
    """Проверить имена, списки ребер и наличие всех вершин."""
    if not isinstance(graph, dict) or not graph:
        message = "тестовый граф должен быть непустым объектом JSON"
        raise RepositoryError(message)
    for name, children in graph.items():
        if not re.fullmatch(r"[A-Z]+", name):
            raise RepositoryError(f"имя тестового пакета: {name}")
        if not isinstance(children, list):
            raise RepositoryError(f"{name}: требуется список зависимостей")
        for child in children:
            if not isinstance(child, str) or child not in graph:
                message = f"{name}: неизвестная зависимость {child}"
                raise RepositoryError(message)
    return graph


def make_repository(settings):
    """Выбрать источник данных из конфигурации."""
    if settings.test_mode:
        return TestRepository(settings.repository, settings.version)
    return NugetRepository(settings.repository, settings.framework)
