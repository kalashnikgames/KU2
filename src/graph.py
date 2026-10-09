"""Построение графа рекурсивным BFS и обнаружение циклов."""

from dataclasses import dataclass, field

from src.models import Package, RepositoryError
from src.versions import normalize_version


@dataclass
class Graph:
    """Корень, ребра и порядок первого обнаружения вершин."""

    root: Package
    edges: dict = field(default_factory=dict)
    discovery: list = field(default_factory=list)


class GraphBuilder:
    """Обходить репозиторий по уровням с рекурсивным переходом."""

    def __init__(self, repository, substring):
        """Подготовить фильтр и таблицу уникальных вершин."""
        self.repository = repository
        self.substring = substring.casefold()
        self.packages = {}
        self.discovered = set()
        self.graph = None

    def excluded(self, name):
        """Проверить непустую подстроку без учета регистра NuGet ID."""
        return bool(self.substring and self.substring in name.casefold())

    def intern(self, package):
        """Получить вершину для имени и версии независимо от регистра."""
        key = (package.name.casefold(), normalize_version(package.version))
        if key not in self.packages:
            self.packages[key] = Package(package.name, key[1])
        return self.packages[key]

    def build(self, root):
        """Построить граф от корня, не запрашивая исключенные пакеты."""
        if self.excluded(root.name):
            raise RepositoryError("корневой пакет исключен фильтром")
        root = self.intern(root)
        self.graph = Graph(root, discovery=[root])
        self.discovered.add(root)
        self.visit_level([root])
        return self.graph

    def visit_level(self, frontier):
        """Обработать весь уровень BFS и рекурсивно перейти к следующему."""
        if not frontier:
            return
        next_frontier = []
        for package in frontier:
            children = []
            for dependency in self.repository.direct(package):
                if self.excluded(dependency.name):
                    continue
                child = self.intern(self.repository.resolve(
                    dependency.name, dependency.constraint
                ))
                if child not in children:
                    children.append(child)
                if child not in self.discovered:
                    self.discovered.add(child)
                    self.graph.discovery.append(child)
                    next_frontier.append(child)
            self.graph.edges[package] = children
        self.visit_level(next_frontier)


def cycle_paths(graph):
    """Найти обратные ребра и вернуть пути циклов, включая петли."""
    visited = set()
    active = []
    cycles = []

    def visit(package):
        """Посетить вершину для диагностики циклов, не для сбора графа."""
        visited.add(package)
        active.append(package)
        for child in graph.edges[package]:
            if child in active:
                cycles.append(active[active.index(child):] + [child])
            elif child not in visited:
                visit(child)
        active.pop()

    visit(graph.root)
    return cycles


def print_graph(graph):
    """Показать порядок BFS, ребра и диагностику циклов этапа 3."""
    print("BFS: " + " -> ".join(package.label for package in graph.discovery))
    for package, children in graph.edges.items():
        targets = ", ".join(child.label for child in children) or "(нет)"
        print(f"{package.label}: {targets}")
    for cycle in cycle_paths(graph):
        print("Цикл: " + " -> ".join(package.label for package in cycle))
