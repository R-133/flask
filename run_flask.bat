@echo off
call venv\Scripts\activate
set FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000
pause
