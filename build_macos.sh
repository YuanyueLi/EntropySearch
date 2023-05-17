#!/bin/bash

# New python environment
python3 -m venv py_env
source py_env/bin/activate
pip install -r requirements.txt

# Build backend
cd backend
pyinstaller -F main.py -n entropy_search_backend.exe
cd ..

# Build frontend
cd frontend
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install yarn
yarn install
yarn run dist
cd ..