#!/bin/sh
echo "Starting hostmanager " && poetry run python hostmanager.py &
echo "Starting web interface " && poetry run python app.py
