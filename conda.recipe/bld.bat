@echo off

cd /D "%RECIPE_DIR%\.."
"%PYTHON%" setup.py install
