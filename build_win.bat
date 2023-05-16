
call py_env\Scripts\activate.bat

cd backend
call pyinstaller -F main.py
cd ..

cd frontend
call yarn run dist