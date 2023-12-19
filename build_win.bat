call python -m venv py_env
call py_env\Scripts\activate.bat
call pip install -r requirements.txt

cd frontend
call yarn install
call yarn run build
cd ..

cd backend
rmdir /S /Q dist
rmdir /S /Q build
call pyinstaller -F main.py -n flash_entropy_search.exe --add-data ../frontend/build:gui -i icon.ico
cd ..
