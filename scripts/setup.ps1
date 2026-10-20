param([string]$Python = "python")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
& $Python -c "import sys; assert sys.version_info[:2] == (3,13), 'Se requiere Python 3.13'"
if ($LASTEXITCODE -ne 0) { throw "Indique la ruta a Python 3.13 mediante -Python" }
& $Python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "No se creó el entorno" }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt -c requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw "Falló la instalación" }
& .\.venv\Scripts\python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw "Dependencias incompatibles" }
