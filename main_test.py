import requests
import json
import urllib.request
from datetime import datetime


class VK:
    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def user_info(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_ids': self.id, 'album_id': 'profile',
                  'extended': 1, 'photo_sizes': 1}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def get_maxsize_photo(self, user_avatars):
        """Метод определяет фото макимального размера, формируем список их url-адресов для выгрузки"""
        avatars = user_avatars['response']['items']
        data_to_file = []
        photo_list = []
        photo_likes_set = set()
        photo_likes_list = []

        for ava in avatars:
            photo_likes = ava['likes']['count']
            photo_likes_set.add(photo_likes)
            photo_likes_list.append(photo_likes)
            photo_date = ava['date']
            max_height = 0
            max_width = 0
            photo_url = ''

            for photo_params in ava['sizes']:
                if photo_params['height'] > max_height:
                    max_height = photo_params['height']
                    max_width = photo_params['width']
                    photo_url = photo_params['url']

            # формируем список фото с кол-во лайков, датой и url-адресами для выгрузки
            photo_list.append({
                'photo_likes': photo_likes,
                'photo_data': photo_date,
                'photo_url': photo_url
            })
        # формируем название и скачиваем файлы на комп
        photo_name = ''
        photo_to_ydisk = []
        for photo in photo_list:
            response = urllib.request.urlopen(photo['photo_url'])
            photo_downloaded = response.read()
            if len(photo_likes_set) == len(photo_likes_list):
                photo_name = f"{photo['photo_likes']}.jpg"
            else:
                photo_name = f"{photo['photo_likes']}_{photo['photo_date']}.jpg"
            with open(f"{photo_name}", 'wb') as file_object:
                file_object.write(photo_downloaded)
            photo_to_ydisk.append({
                'photo_name': photo_name,
                'photo_url': photo['photo_url']
            })

        # формируем данные для файла json)
        data_to_file.append({
            "file_name": photo_url.split('/')[7].split('?')[0],
            "size": max_height,
            "height": max_height,
            "width": max_width
        })
        with open('photos.json', 'w') as f:
            json.dump(data_to_file, f)
        return photo_to_ydisk


class YaUploader:
    """Метод загружает файл на яндекс диск"""

    def __init__(self, token: str):
        self.token = token

    def create_dir(self, dir_name):
        print(dir_name)
        url = f"https://cloud-api.yandex.net/v1/disk/resources?path={dir_name}"
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json', 'Authorization': f'OAuth {self.token}'}
        response = requests.put(url, headers=headers)
        dir = response.json()

    def upload(self, dir_name, photos, photos_default=5):
        """Метод загружает файл на яндекс диск"""
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json', 'Authorization': f'OAuth {self.token}'}
        # фиксируем кол-во фото
        if len(photos) > photos_default:
            photos_default = photos[0:photos_default]
        else:
            photos_default = photos
        print(dir_name)
        for photo in photos_default:
            URL = "https://cloud-api.yandex.net/v1/disk/resources"
            response = requests.get(
                f"{URL}/upload?path={dir_name}/{photo['photo_name']}", headers=headers)
            print("--> ", response.json())
            url_for_loading = response.json()["href"]
            message = ''

            with open(str(photo['photo_name']), 'rb') as f:
                response = requests.put(
                    url_for_loading, headers=headers, files={"file": f})
                if response.status_code == 201:
                    message = f"File {photo['photo_name']} downloaded successfully"
                else:
                    message = f"File {photo['photo_name']} not downloaded"
            # логирование загрузки фото
            with open('logging.txt', 'a') as log_f:
                log_f.write(
                    f"{str(datetime.now()).split('.')[0]} - {message}\n")


if __name__ == '__main__':
    access_vk_token = ''
    access_ydisk_token = ''

    with open('token.txt', 'r') as f:
        access_vk_token = f.readline().strip()
        access_ydisk_token = f.readline().strip()

    USER_ID = '253472352'
    vk = VK(access_vk_token, USER_ID)
    response_info = vk.user_info()
    max_photos = vk.get_maxsize_photo(response_info)

    dir_name = f"avatar_vk_{str(datetime.now()).split('.')[0].replace(':','_')}"
    uploader = YaUploader(access_ydisk_token)
    uploader.create_dir(dir_name)
    result = uploader.upload(dir_name, max_photos)
