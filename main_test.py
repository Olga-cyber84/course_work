import requests
import json
import urllib.request
from datetime import datetime
from pprint import pprint
import sys


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
        pprint(response.json())
        return response

    def get_maxsize_photo(self):
        """Метод определяет фото макимального размера, формируем список их url-адресов для выгрузки"""
        user_info = self.user_info()
        if user_info.status_code == 200:
            avatars = user_info.json()['response']['items']
            data_to_file = []
            photo_list = []
            photo_likes_uniq = set()
            photo_list_corr = []

            for ava in avatars:
                photo_likes = ava['likes']['count']
                photo_likes_uniq.add(photo_likes)
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
                one_photo = {
                    'photo_name': photo_likes,
                    'photo_data': photo_date,
                    'photo_url': photo_url
                }

                photo_list.append(one_photo)
            # формируем список фото с уникальыми названиями и url-адресами для выгрузки
            if len(photo_likes_uniq) < len(photo_list):
                for photo in photo_list:
                    if photo['photo_name'] in photo_likes_uniq:
                        photo_list_corr.append(
                            {'photo_name': str(photo['photo_name']) + "_" + str(photo['photo_data']), 'photo_url': photo['photo_url']})
                    else:
                        photo_list_corr.append(
                            {'photo_name': str(photo['photo_name']), 'photo_url': photo['photo_url']})
            else:
                photo_list_corr = photo_list
            print(photo_list_corr)
            # формируем название и скачиваем файлы на комп

            photo_to_ydisk = []
            for photo in photo_list_corr:
                response = urllib.request.urlopen(photo['photo_url'])
                photo_downloaded = response.read()

                with open(f"{photo['photo_name']}", 'wb') as file_object:
                    file_object.write(photo_downloaded)
                photo_to_ydisk.append({
                    'photo_name': photo['photo_name'],
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
        else:
            print(
                "ОШИБКА получения данных пользователя. Обратитесь к разработчику приложения")
            sys.exit()


class YaUploader:
    """Класс загружает файл на яндекс диск"""

    def __init__(self, token: str):
        self.token = token

    def create_dir(self, dir_name):
        url = f"https://cloud-api.yandex.net/v1/disk/resources?path={dir_name}"
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json', 'Authorization': f'OAuth {self.token}'}
        response = requests.put(url, headers=headers)
        if response.status_code == 201:
            print("Папка на Яндекс Диске создана")
            return True
        else:
            print(
                "ОШИБКА! Не создана папка на Яндекс Диске. Обратитесь к разработчику приложения.")
            sys.exit()

    def upload(self, dir_name, photos, photos_default=5):
        """Метод загружает файл на яндекс диск"""
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json', 'Authorization': f'OAuth {self.token}'}
        # фиксируем кол-во фото
        if len(photos) > photos_default:
            photos = photos[0:photos_default]
        print(dir_name)
        for photo in photos:
            URL = "https://cloud-api.yandex.net/v1/disk/resources"
            params = f"{URL}/upload?path={dir_name}/{photo['photo_name']}.jpg&url={photo['photo_url']}"
            print("params -->>> ", params)
            response = requests.post(params, headers=headers)
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
        # return response.json()


if __name__ == '__main__':
    access_vk_token = ''
    access_ydisk_token = ''

    with open('token.txt', 'r') as f:
        access_vk_token = f.readline().strip()
        access_ydisk_token = f.readline().strip()

    USER_ID = '253472352'
    vk = VK(access_vk_token, USER_ID)
    vk.user_info()
    max_photos = vk.get_maxsize_photo()

    dir_name = f"avatar_vk_{str(datetime.now()).split('.')[0].replace(':','_').replace(' ','_')}"
    uploader = YaUploader(access_ydisk_token)
    creat_dir_res = uploader.create_dir(dir_name)
    if creat_dir_res:
        result = uploader.upload(dir_name, max_photos)
        print("ЗАГРУЗКА ЗАВЕРШЕНА")
