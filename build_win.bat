
call py_env\Scripts\activate.bat
call pip install -r requirements.txt

cd backend
call pyinstaller -F main.py -n entropy_search_backend.exe
cd ..

cd frontend
call yarn run dist