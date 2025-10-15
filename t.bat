@echo off
cls
python .\ejecutar_tests.py
python comparador_logs.py
del logs\*.* /Q