import requests

def send_push_notification(token, title, body, image_url=None, farmland=None, camera=None, animal=None):
    message = {
        'to': token,
        'sound': 'default',
        'title': title,
        'body': body,
        'data': {
            'image_url': image_url or '',
            'farmland': farmland or 'Тодорхойгүй',
            'camera': camera or '0',
            'animal': animal or 'Тодорхойгүй'
        },
    }

    response = requests.post(
        'https://exp.host/--/api/v2/push/send',
        json=message,
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    )

    print(f'Notification sent: {response.status_code}, {response.text}')
