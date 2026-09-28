@echo off
cd /d "%~dp0\.."
python -B -m src.cli examples\newtonsoft.toml
python -B -m src.cli examples\configuration.toml
python -B -m src.cli examples\logging.toml
