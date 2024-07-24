#!/bin/bash

# 環境変数の設定（必要に応じて修正）
export FLASK_APP=app.py
export FLASK_ENV=production

# Gunicornの起動
gunicorn -w 4 -b 0.0.0.0:8000 app:app
