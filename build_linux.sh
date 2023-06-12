#!/bin/bash

# New python environment
/bin/rm -rf py_env
python3 -m venv py_env
source py_env/bin/activate
pip install -r requirements.txt

# Build backend
cd backend
pyinstaller -F main.py -n entropy_search_backend
cd ..

# Build frontend
cd frontend
yarn install
yarn run dist
cd ..