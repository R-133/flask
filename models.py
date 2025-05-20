from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
import json

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(8),unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    farms = db.relationship(
    'Farm',
    back_populates='owner',
    cascade='all, delete-orphan',
    lazy=True
    )

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Farm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True) 
    location = db.Column(db.Text, nullable=True)

    owner = db.relationship('User', back_populates='farms')
    cameras = db.relationship(
        'Camera',
        backref='farm',
        cascade='all, delete-orphan',
        lazy=True
    )

    def __repr__(self):
        return f"Farm('{self.name}', '{self.image_url}')"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'image_url': self.image_url,
            'location': json.loads(self.location) if self.location else None,
            'cameras': [camera.to_dict() for camera in self.cameras] 
        }



class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    camera_name = db.Column(db.String(100), nullable=False)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    camera_url = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100), nullable=True)  
    direction = db.Column(db.String(20), nullable=True)   
    notifications = db.relationship(
        'Notification',
        back_populates='camera',
        cascade='all, delete-orphan',
        lazy=True
    )

    def __repr__(self):
        return f"Camera('{self.camera_name}', '{self.camera_url}')"

    def to_dict(self):
        return {
            'id': self.id,
            'camera_name': self.camera_name,
            'farm_id': self.farm_id,
            'camera_url': self.camera_url,
            'location': self.location,
            'direction': self.direction,
            'notifications': [notification.to_dict() for notification in self.notifications]  
        }



class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

    camera = db.relationship('Camera', back_populates='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'camera_id': self.camera_id,
            'image_url': self.image_url,
        }


class UserToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)  
    token = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<UserToken {self.user_id}: {self.token}>'
