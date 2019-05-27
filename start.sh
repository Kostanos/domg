#!/bin/bash
echo "Starting hostmanager " && python -u hostmanager.py &
echo "Starting web interface " && python -u app.py
