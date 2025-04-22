from flask import current_app
from models import Camera, Farm, UserToken

def get_tokens_by_camera(camera_id):
    camera = Camera.query.get(camera_id)
    
    if not camera:
        current_app.logger.warning(f'Камера олдсонгүй: {camera_id}')
        return []

    farm = Farm.query.get(camera.farm_id)
    if not farm:
        current_app.logger.warning(f'Фарм олдсонгүй: {camera.farm_id}')
        return []

    user_tokens = UserToken.query.filter_by(user_id=farm.user_id).all()

    tokens = [user_token.token for user_token in user_tokens if user_token.token]

    return tokens


def get_farmland_and_camera_name(camera_id):
    camera = Camera.query.get(camera_id)
    if not camera:
        current_app.logger.warning(f'Камера олдсонгүй: {camera_id}')
        return None, None

    farm = Farm.query.get(camera.farm_id)
    if not farm:
        current_app.logger.warning(f'Фарм олдсонгүй: {camera.farm_id}')
        return None, None
    

    return farm.name, camera.camera_name