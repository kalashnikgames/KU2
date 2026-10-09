"""Проверка TOML-конфигурации инструмента."""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


REQUIRED_KEYS = {
    "package", "repository", "test_mode", "version", "output", "filter",
}
PACKAGE_PATTERN = r"[A-Za-z0-9_.-]+"
VERSION_PATTERN = r"\d+(?:\.\d+){0,3}(?:-[0-9A-Za-z.-]+)?(?:\+[\w.-]+)?"


class ConfigError(Exception):
    """Некорректный файл или значение конфигурации."""


@dataclass(frozen=True)
class Settings:
    """Проверенные параметры запуска."""

    package: str
    repository: str
    test_mode: bool
    version: str
    output: Path
    filter: str
    framework: str = "net8.0"


def require_text(values, key, allow_empty=False):
    """Проверить тип и содержимое строкового параметра."""
    value = values[key]
    if not isinstance(value, str):
        raise ConfigError(f"{key}: требуется строка")
    if not allow_empty and not value.strip():
        raise ConfigError(f"{key}: значение не может быть пустым")
    return value


def validate_repository(value, test_mode, base):
    """Проверить адрес NuGet или файл тестового графа."""
    if test_mode:
        path = Path(value).expanduser()
        path = path if path.is_absolute() else base / path
        if not path.is_file():
            raise ConfigError(f"repository: файл не найден: {path}")
        return str(path.resolve())
    url = urlsplit(value)
    if url.scheme not in ("https", "http") or not url.hostname:
        raise ConfigError("repository: требуется HTTP(S)-адрес NuGet V3")
    return value


def validate_values(values, base):
    """Проверить все поля и получить настройки."""
    missing = REQUIRED_KEYS - values.keys()
    unknown = values.keys() - REQUIRED_KEYS - {"framework"}
    if missing or unknown:
        message = f"поля: отсутствуют {sorted(missing)}"
        raise ConfigError(f"{message}, лишние {sorted(unknown)}")
    if type(values["test_mode"]) is not bool:
        raise ConfigError("test_mode: требуется true или false")
    package = require_text(values, "package")
    pattern = r"[A-Z]+" if values["test_mode"] else PACKAGE_PATTERN
    if not re.fullmatch(pattern, package):
        raise ConfigError("package: недопустимое имя пакета")
    version = require_text(values, "version")
    if not re.fullmatch(VERSION_PATTERN, version):
        raise ConfigError("version: требуется конкретная версия NuGet")
    repository = validate_repository(
        require_text(values, "repository"), values["test_mode"], base
    )
    output = validate_output(require_text(values, "output"), base)
    substring = require_text(values, "filter", allow_empty=True)
    framework = values.get("framework", "net8.0")
    valid_framework = isinstance(framework, str)
    valid_framework = valid_framework and re.fullmatch(r"net[89]\.0",
                                                       framework)
    if not valid_framework:
        raise ConfigError("framework: поддерживаются net8.0 и net9.0")
    return Settings(package, repository, values["test_mode"], version,
                    output, substring, framework)


def validate_output(value, base):
    """Проверить имя будущего PNG, не создавая файл."""
    path = Path(value).expanduser()
    path = path if path.is_absolute() else base / path
    if path.suffix.lower() != ".png" or path.is_dir():
        raise ConfigError("output: требуется имя файла с расширением .png")
    ancestor = path.parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    if not ancestor.is_dir():
        raise ConfigError("output: родительский путь не является каталогом")
    return path.resolve()


def load_settings(path):
    """Прочитать TOML и разрешить пути относительно его каталога."""
    path = Path(path).resolve()
    try:
        with path.open("rb") as stream:
            values = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as error:
        message = f"config: не удалось прочитать {path}: {error}"
        raise ConfigError(message) from error
    return validate_values(values, path.parent)
