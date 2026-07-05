# Ejecutar comprobaciones del proyecto Django + Flake8 + Vulture
check:
    mypy .
    flake8 --count **/*.py
    ruff check .
    vulture . --exclude .venv/


# Borrar ficheros temporales y espurios
clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -exec rm -r "{}" \;
    find . -type d -name ".sass-cache" -exec rm -r "{}" \;


# Muestas las versiones de Python y Django
versions:
    python -V
    python -c "import django; print(django.__version__)"
    psql --version
    python -m site

# Ejecutar los test pasados como parámetro (Empezará por el último que haya fallado)
test *args='.':
    python3 -m pytest --failed-first -x --log-cli-level=INFO --doctest-modules -m "not slow" {{ args }}

# Muestra información del Harware / S.O. / Python / Django
info:
    @echo "This is an {{arch()}} machine"
    @echo "OS: {{os()}} / {{os_family()}}"
    python3 -V
    uptime

tags:
    ctags -R --exclude=@ctags-exclude-names.txt .
