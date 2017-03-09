@echo off

cd /D "%RECIPE_DIR%\.."
"%PYTHON%" setup.py install --single-version-externally-managed --record=record.txt
