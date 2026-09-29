name: Bot Cripto 247

on:
  schedule:
    - cron: '2,17,32,47 * * * *'  # Ejecuta a los 2 minutos de cerrar cada vela de 15 min
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - name: Clonar repositorio
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Restaurar memoria del Bot (Caché Antispam)
        uses: actions/cache@v4
        with:
          path: last_state.json
          key: bot-state-cache

      - name: Instalar librerías
        run: pip install -r requirements.txt

      - name: Ejecutar Bot
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python bot_cripto.py
