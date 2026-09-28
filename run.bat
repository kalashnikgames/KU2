@echo off
cd /d "%~dp0"
python -B -m src.cli %*
