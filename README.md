# Twitch Streams GUI

App desktop desenvolvido em python e com a interface feita em KiviMD.

O programa exibe na tela todas streams ao vivo seguidas pelo usuário, e permite
assistir uma live no reprodutor de vídeo Vlc.

## Instalar dependencias

```
poetry install
```

## Rodar App

```
poetry shell

poetry run python app/main.py
```

## Rodar testes

```
poetry run pytest
```

## Coverage

```
coverage run -m pytest

coverage report --include=app/boximg.py,app/boxmain.py,app/popupprogress.py,app/main.py

coverage html --include=app/main.py,app/boximg.py,app/boxmain.py,app/popupprogress.py
```
