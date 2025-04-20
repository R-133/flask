venv\Scripts\activate
set FLASK_APP=app.py

flask run --host=0.0.0.0 --port=5000

flask db init
flask db migrate
flask db upgrade



flask db downgrade  
flask db upgrade    
