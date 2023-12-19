call python -m venv py_env
call py_env\Scripts\activate.bat
call pip install -r requirements.txt

cd backend
rmdir /S /Q dist
rmdir /S /Q build
call pyinstaller -F main.py -n flash_entropy_search.exe --add-data ../new_frontend/gui:gui -i icon.ico
cd ..

cd frontend
call yarn install
call yarn run dist
cd ..