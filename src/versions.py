"""Самостоятельная обработка версий и диапазонов NuGet."""

from src.models import RepositoryError


RELEASE_PART_COUNT = 4
NORMAL_PART_COUNT = 3


def version_key(text):
    """Построить ключ порядка NuGet/SemVer без готовых библиотек."""
    core = text.split("+", maxsplit=1)[0]
    release, separator, prerelease = core.partition("-")
    try:
        numbers = tuple(int(part) for part in release.split("."))
    except ValueError as error:
        raise RepositoryError(f"неверная версия: {text}") from error
    if not numbers or len(numbers) > RELEASE_PART_COUNT:
        raise RepositoryError(f"неверная версия: {text}")
    padded = numbers + (0,) * (RELEASE_PART_COUNT - len(numbers))
    labels = tuple(
        (0, int(part)) if part.isdigit() else (1, part.lower())
        for part in prerelease.split(".")
    ) if separator else ()
    return padded, not separator, labels


def normalize_version(text):
    """Убрать метаданные, ведущие нули и лишний нулевой четвертый сегмент."""
    numbers, _, _ = version_key(text)
    release = list(numbers)
    if not release[-1]:
        release.pop()
    normalized = ".".join(str(part) for part in release)
    core = text.split("+", maxsplit=1)[0]
    _, separator, prerelease = core.partition("-")
    return normalized + ("-" + prerelease.lower() if separator else "")


def range_bounds(constraint):
    """Разобрать точную версию, минимум или интервальную запись NuGet."""
    text = constraint.strip()
    if not text or text == "*":
        return None, None, True, True
    if text.startswith(("[", "(")):
        if not text.endswith(("]", ")")):
            raise RepositoryError(f"неверный диапазон: {text}")
        inner = text[1:-1]
        if "," not in inner:
            if not text.startswith("[") or not text.endswith("]"):
                raise RepositoryError(f"неверная точная версия: {text}")
            return inner, inner, True, True
        lower, upper = inner.split(",", maxsplit=1)
        return (lower.strip() or None, upper.strip() or None,
                text[0] == "[", text[-1] == "]")
    return text, None, True, True


def constraint_predicate(constraints):
    """Пересечь диапазоны и показать их наиболее строгие границы."""
    lower = upper = None
    include_lower = include_upper = True
    for constraint in constraints:
        candidate_lower, candidate_upper, lower_inclusive, upper_inclusive = (
            range_bounds(constraint)
        )
        if candidate_lower is not None:
            if lower is None or version_key(candidate_lower) > version_key(lower):
                lower, include_lower = candidate_lower, lower_inclusive
            elif version_key(candidate_lower) == version_key(lower):
                include_lower = include_lower and lower_inclusive
        if candidate_upper is not None:
            if upper is None or version_key(candidate_upper) < version_key(upper):
                upper, include_upper = candidate_upper, upper_inclusive
            elif version_key(candidate_upper) == version_key(upper):
                include_upper = include_upper and upper_inclusive
    if (lower is not None and upper is not None
            and version_key(lower) == version_key(upper)
            and include_lower and include_upper):
        return f"={lower}"
    bounds = []
    if lower is not None:
        bounds.append(f"{'>=' if include_lower else '>'}{lower}")
    if upper is not None:
        bounds.append(f"{'<=' if include_upper else '<'}{upper}")
    return ", ".join(bounds) or "*"


def satisfies(version, constraint):
    """Проверить границы; не выбирать prerelease без явного разрешения."""
    key = version_key(version)
    if "-" in version and "-" not in constraint:
        return False
    lower, upper, include_lower, include_upper = range_bounds(constraint)
    return meets_lower(key, lower, include_lower) and meets_upper(
        key, upper, include_upper
    )


def meets_lower(key, lower, inclusive):
    """Проверить нижнюю границу диапазона."""
    if lower is None:
        return True
    boundary = version_key(lower)
    return key > boundary or (inclusive and key == boundary)


def meets_upper(key, upper, inclusive):
    """Проверить верхнюю границу диапазона."""
    if upper is None:
        return True
    boundary = version_key(upper)
    return key < boundary or (inclusive and key == boundary)


def resolve_version(versions, constraint):
    """Выбрать минимальную доступную подходящую версию."""
    candidates = (
        version for version in versions if satisfies(version, constraint)
    )
    result = min(candidates, key=version_key, default=None)
    if result is None:
        raise RepositoryError(f"нет версии, удовлетворяющей {constraint}")
    return normalize_version(result)
