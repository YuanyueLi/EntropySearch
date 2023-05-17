#!/bin/bash

# New python environment
python -m venv py_env
source py_env/bin/activate
pip install -r requirements.txt

# Build backend
cd backend
pyinstaller -F main.py -n entropy_search_backend.exe
cd ..

# Build frontend
cd frontend
yarn install
yarn run dist
cd ..