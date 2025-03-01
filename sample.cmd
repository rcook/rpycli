@echo off
setlocal
set PYTHONPATH=%~dp0
python.exe "rpycli\sample\main.py" %*
