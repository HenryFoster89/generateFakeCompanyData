@echo off
python -m venv venv
call venv\Scripts\activate
pip install ".[dev]"
echo Setup completato!
pause