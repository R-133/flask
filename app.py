from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token 
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import jwt_required


from werkzeug.utils import secure_filename


# Flask тохиргоо
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite өгөгдлийн сан
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # JWT нууц түлхүүр

# CORS тохиргоо (бүх хандалтыг зөвшөөрнө)
CORS(app)

# Өгөгдлийн сан, bcrypt, JWT тохиргоо
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

from models import User
from models import Farm, Camera



@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not all(field in data for field in ['username', 'email', 'phone', 'password']):
        return jsonify({"message": "Бүх талбарыг бөглөнө үү!"}), 400

    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"message": "Энэ и-мэйл бүртгэгдсэн байна!"}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    new_user = User(
        username=data['username'],
        email=data['email'],
        phone=data['phone'],
        password=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Хэрэглэгч амжилттай бүртгэгдлээ!"}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify(message="И-мэйл болон нууц үг заавал шаардлагатай!"), 400

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id, additional_claims={"sub": str(user.id)})
        return jsonify(
            access_token=access_token, 
            user_id=user.id
            ), 200

    return jsonify(message="И-мэйл эсвэл нууц үг буруу байна."), 401


from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route('/user', methods=['GET'])
@jwt_required() 
def get_user_info():
    user_id = get_jwt_identity()  # JWT-аас хэрэглэгчийн ID-г авна
    user = User.query.get(user_id)
    
    if user:
        user_data = {
            'username': user.username,
            'phone': user.phone,
            'email': user.email
        }
        return jsonify(user_data=user_data), 200
    return jsonify(message="User not found"), 404


@app.route('/user', methods=['PUT'])
@jwt_required()
def update_user_info():
    user_id = get_jwt_identity()  
    user = User.query.get(user_id)

    if not user:
        return jsonify(message="User not found"), 404

    data = request.get_json()

    # Шинэ утгуудыг set хийх
    user.username = data.get('username', user.username)
    user.phone = data.get('phone', user.phone)
    user.email = data.get('email', user.email)

    db.session.commit()

    return jsonify(message="User updated successfully!"), 200

@app.route('/user/password', methods=['PUT'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify(message="User not found"), 404

    data = request.get_json()

    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify(message="Бүх талбарыг бөглөнө үү!"), 400

    if not bcrypt.check_password_hash(user.password, current_password):
        return jsonify(message="Одоогийн нууц үг буруу байна!"), 400

    user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()

    return jsonify(message="Нууц үг амжилттай солигдлоо!"), 200


UPLOAD_FOLDER = 'path_to_your_upload_folder'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Зураг форматыг зөвшөөрөх
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_farm', methods=['POST'])
@jwt_required()  # JWT токен шаардлагатай
def add_farm():
    try:
        data = request.get_json()
        if not data.get('name'):
            return jsonify({'message': 'Farm name is required!'}), 400

        user_id = get_jwt_identity()  

        farm = Farm(
            name=data['name'],
            user_id=user_id,
            image_url=data.get('image_url')
        )

        db.session.add(farm)
        db.session.commit()

        return jsonify({
            'message': 'Farm added successfully!',
            'farm': farm.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/farmlands', methods=['GET'])
@jwt_required()
def get_farmlands():
    user_id = get_jwt_identity()
    farmlands = Farm.query.filter_by(user_id=user_id).all()

    return jsonify({
        'farmlands': [f.to_dict() for f in farmlands]
    }), 200

@app.route('/add_camera', methods=['POST'])
@jwt_required()  # Заавал JWT токен авах
def add_camera():
    try:
        data = request.get_json()

        if not data.get('camera_name') or not data.get('camera_url') or not data.get('farm_id'):
            return jsonify({'message': 'Camera name, URL болон Farm ID шаардлагатай!'}), 400

        # Камера үүсгэх
        camera = Camera(
            camera_name=data['camera_name'],
            farm_id=data['farm_id'],
            camera_url=data['camera_url']
        )

        db.session.add(camera)
        db.session.commit()

        return jsonify({
            'message': 'Камер амжилттай нэмэгдлээ!',
            'camera': camera.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/cameras', methods=['GET'])
@jwt_required()
def get_cameras():
    user_id = get_jwt_identity()
    farms = Farm.query.filter_by(user_id=user_id).all()
    farm_ids = [farm.id for farm in farms]

    cameras = Camera.query.filter(Camera.farm_id.in_(farm_ids)).all()

    return jsonify({
        'cameras': [camera.to_dict() for camera in cameras]
    }), 200




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
