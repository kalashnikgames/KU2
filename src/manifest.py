"""Чтение прямых зависимостей из XML NuGet .nuspec."""

import re
import xml.etree.ElementTree as etree

from src.models import Dependency, RepositoryError


STANDARD_LIMIT = (2, 1)
MODERN_NET_MINIMUM = 5


def local_name(element):
    """Вернуть имя XML-тега без пространства имен."""
    return element.tag.rsplit("}", maxsplit=1)[-1]


def framework_score(value, target):
    """Оценить совместимость групп net/netstandard для net8 или net9."""
    name = value.lower().replace(".netstandard", "netstandard")
    name = name.replace(".netcoreapp", "net").replace("netcoreapp", "net")
    if not name:
        return (0, ())
    match = re.fullmatch(r"(netstandard|net)(\d+)\.(\d+)", name)
    if not match:
        return None
    kind, major, minor = match.groups()
    version = (int(major), int(minor))
    target_version = tuple(int(part) for part in target[3:].split("."))
    if kind == "netstandard" and version <= STANDARD_LIMIT:
        return (1, version)
    if kind == "net" and version <= target_version:
        score = 3 if version[0] >= MODERN_NET_MINIMUM else 2
        return (score, version)
    return None


def select_group(groups, framework):
    """Выбрать наиболее подходящую группу, не объединяя разные TFM."""
    scored = []
    for group in groups:
        score = framework_score(group.get("targetFramework", ""), framework)
        if score is not None:
            scored.append((score, group))
    if not scored:
        raise RepositoryError(f"нет группы зависимостей для {framework}")
    return max(scored, key=lambda pair: pair[0])[1]


def parse_manifest(data, framework):
    """Получить зависимости выбранной группы из .nuspec."""
    try:
        root = etree.fromstring(data)
    except etree.ParseError as error:
        raise RepositoryError(f"ошибка XML .nuspec: {error}") from error
    dependencies = next(
        (item for item in root.iter() if local_name(item) == "dependencies"),
        None,
    )
    if dependencies is None:
        return []
    groups = [item for item in dependencies if local_name(item) == "group"]
    parent = select_group(groups, framework) if groups else dependencies
    return read_dependencies(parent)


def read_dependencies(parent):
    """Получить список имен и диапазонов из выбранного XML-элемента."""
    result = []
    for item in parent:
        if local_name(item) == "dependency":
            name = item.get("id")
            if not name:
                raise RepositoryError("у зависимости отсутствует id")
            result.append(Dependency(name, item.get("version", "*")))
    return result
