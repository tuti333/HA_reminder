#!/usr/bin/with-contenv bashio

echo "hello world"

uvicorn app.main:app --host 0.0.0.0 --port 8080

