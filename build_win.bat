call python3 -m venv py_env
call py_env\Scripts\activate.bat
call pip install -r requirements.txt

cd backend
call pyinstaller -F main.py -n entropy_search_backend.exe
cd ..

cd frontend
call yarn install
call yarn run dist
cd ..