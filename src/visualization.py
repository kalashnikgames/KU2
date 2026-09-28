"""Текст Mermaid и PNG, отрисованный настоящим Mermaid CLI."""

import html
import json
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


LABEL_WIDTH = 32
RENDER_TIMEOUT = 120
ERROR_TEXT_LIMIT = 2000
PNG_HEADER = b"\x89PNG\r\n\x1a\n"
PNG_METADATA_SIZE = 24


class RenderError(Exception):
    """Ошибка отрисовки или записи изображения."""


def package_label(package):
    """Разбить длинное имя по точкам и безопасно подписать вершину."""
    lines = []
    current = ""
    for part in package.name.split("."):
        candidate = current + "." + part if current else part
        if current and len(candidate) > LABEL_WIDTH:
            lines.append(current + ".")
            current = part
        else:
            current = candidate
    lines.extend([current, package.version])
    return "<br/>".join(html.escape(line, quote=True) for line in lines)


def to_mermaid(graph):
    """Описать все вершины и ребра, включая петли, в Mermaid flowchart."""
    identifiers = {package: f"N{index}"
                   for index, package in enumerate(graph.discovery)}
    lines = ["flowchart LR"]
    for package in graph.discovery:
        label = package_label(package)
        identifier = identifiers[package]
        lines.append(f'    {identifier}["{label}"]')
    for package, children in graph.edges.items():
        for child in children:
            lines.append(f"    {identifiers[package]} --> {identifiers[child]}")
    lines.append("    classDef root fill:#dbeafe,stroke:#1d4ed8,"
                 "stroke-width:3px")
    lines.append(f"    class {identifiers[graph.root]} root")
    return "\n".join(lines) + "\n"


def renderer_command():
    """Найти Node и локальный Mermaid CLI либо путь из MERMAID_CLI."""
    root = Path(__file__).resolve().parent.parent
    default = root / "node_modules/@mermaid-js/mermaid-cli/src/cli.js"
    cli = Path(os.environ.get("MERMAID_CLI", str(default)))
    node = shutil.which("node")
    if not node or not cli.is_file():
        raise RenderError("нужны Node.js и Mermaid CLI: выполните npm install")
    return [node, str(cli.resolve())]


def browser_path():
    """Учесть явный браузер и обычные пути Chrome/Edge в Windows."""
    explicit = os.environ.get("MERMAID_BROWSER")
    if explicit:
        return explicit
    candidates = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        / "Microsoft/Edge/Application/msedge.exe",
    ]
    return next((str(path) for path in candidates if path.is_file()), None)


def png_size(path):
    """Проверить сигнатуру PNG и прочитать ширину с высотой из IHDR."""
    with Path(path).open("rb") as stream:
        header = stream.read(PNG_METADATA_SIZE)
    if not header.startswith(PNG_HEADER) or header[12:16] != b"IHDR":
        raise RenderError("рендерер не создал корректный PNG")
    try:
        return struct.unpack(">II", header[16:PNG_METADATA_SIZE])
    except struct.error as error:
        raise RenderError("поврежденный заголовок PNG") from error


def render_png(source, output):
    """Запустить Mermaid CLI с безопасными отдельными аргументами."""
    command = renderer_command() + [
        "-i", str(source), "-o", str(output), "-t", "neutral",
        "-b", "white", "-s", "2",
    ]
    with tempfile.TemporaryDirectory() as directory:
        browser = browser_path()
        if browser:
            config = Path(directory) / "puppeteer.json"
            config.write_text(json.dumps({"executablePath": browser}),
                              encoding="utf-8")
            command.extend(["-p", str(config)])
        try:
            subprocess.run(command, check=True, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=RENDER_TIMEOUT)
        except subprocess.CalledProcessError as error:
            message = (error.stderr or error.stdout)[-ERROR_TEXT_LIMIT:]
            raise RenderError(f"Mermaid CLI: {message.strip()}") from error
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RenderError(f"Mermaid CLI: {error}") from error
    png_size(output)


def save_visualization(graph, output):
    """Сохранить .mmd и атомарно заменить PNG после успешной отрисовки."""
    source = output.with_suffix(".mmd")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(to_mermaid(graph), encoding="utf-8")
        with tempfile.TemporaryDirectory(dir=output.parent) as directory:
            temporary = Path(directory) / "graph.png"
            render_png(source, temporary)
            os.replace(temporary, output)
    except OSError as error:
        raise RenderError(f"не удалось записать граф: {error}") from error
    return source, output
