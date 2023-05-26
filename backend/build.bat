rmdir /S /Q dist
rmdir /S /Q build
call ..\py_env\Scripts\activate.bat
call pyinstaller -F main.py