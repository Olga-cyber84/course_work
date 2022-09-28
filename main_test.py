import requests
from pprint import pprint
import json
import urllib.request

access_token = ''
with open('token.txt', 'r') as f:
    access_token = f.read().strip()

user_id = '253472352'


class VK:
    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_ids': self.id, 'album_id': 'profile',
                  'extended': 1, 'photo_sizes': 1}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def get_max_photo(self, user_avatars):
        avatars = user_avatars['response']['items']
        data_to_file = []
        photo_url_list = []
        for item, photo in enumerate(avatars):
            photo_likes = photo['likes']['count']
            photo_date = photo['date']
            max_height = 0
            max_width = 0
            photo_url = ''

            for photo_params in photo['sizes']:
                if photo_params['height'] > max_height:
                    max_height = photo_params['height']
                    max_width = photo_params['width']
                    photo_url = photo_params['url']
            photo_url_list.append(photo_url)

            url = photo_url
            response = urllib.request.urlopen(url)
            data = response.read()

            with open(f'avatar_{item+1}.jpg', 'wb') as file_object:
                file_object.write(data)
            data_to_file.append({
                "file_name": photo_url.split('/')[7].split('?')[0],
                "size": max_height,
                "height": max_height,
                "width": max_width
            })
        with open('photos.json', 'w') as f:
            json.dump(data_to_file, f)
        return photo_url_list


class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def create_dir(self, dir_name):
        url = f"https://cloud-api.yandex.net/v1/disk/resources?path={dir_name}"
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json', 'Authorization': f'OAuth {self.token}'}
        response = requests.put(url, headers=headers)
        dir = response.json()
        print(dir)

    def upload(self, dir_name, photos):
        """Метод загружает файл на яндекс диск"""
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json', 'Authorization': f'OAuth {self.token}'}
        photo_quantity_default = 5
        if len(photos) > 5:
            photos_default = photos[0:5]
        else:
            photos_default = photos
        for item in range(len(photos_default)):
            URL = "https://cloud-api.yandex.net/v1/disk/resources"

            with open(photos_default[item], 'wb') as f:
                response = requests.post(
                    f'{URL}/upload?path={dir_name}/avatar_{int(item)+1}&url={photos_default[item]}', headers=headers, files={"file": f})

                print(response.json())


if __name__ == '__main__':
    vk = VK(access_token, user_id)
    response_info = vk.users_info()
    max_photos = vk.get_max_photo(response_info)

    dir_name = "avatar_vk"
    token = "y0_AgAAAAAiqXYTAADLWwAAAADOBUkiVF9IpvSKR963QnUj16X92F_-LHE"
    uploader = YaUploader(token)
    # uploader.create_dir(dir_name)
    result = uploader.upload(dir_name, max_photos)
