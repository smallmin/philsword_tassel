# -*- coding: utf-8 -*-
from fileinput import filename
import sys, os
import requests
import json
from PIL import Image
import hashlib

# 忽略 ssl 不验证警告
from requests.packages import urllib3
urllib3.disable_warnings()

BASE_DIR = sys.path[0]

# token get by http://philsword.com/keysword/main
IMAGE_PUT_TOKEN = 'philsword_token'

IMAGE_COMPRESS_DIR = BASE_DIR + '/images/compress/'
IMAGE_COPYED_DIR = BASE_DIR + '/images/copyed/'

IMAGE_PUT_HOST = 'philsword.com'
IMAGE_GET_HOST = 'philsword.com'
IMAGE_PUT_URL = 'http://' + IMAGE_PUT_HOST + '/upimg'
IMAGE_GET_URL = 'http://' + IMAGE_GET_HOST + '/img'

if not os.path.exists(IMAGE_COMPRESS_DIR):
    os.makedirs(IMAGE_COMPRESS_DIR)
if not os.path.exists(IMAGE_COPYED_DIR):
    os.makedirs(IMAGE_COPYED_DIR)

def get_file_size(file):
    # 获取文件大小:KB
    size = os.path.getsize(file)
    return size / 1024

def get_file_name_suffix(file):
    basename = os.path.basename(file)
    items = basename.split('.')
    name = ''.join(items[:-1])
    suffix = items[-1]
    return name, suffix

def compress_image(infile, outfile=None, goalkb=100, step=10, quality=80):
    name, suffix = get_file_name_suffix(infile)
    if suffix not in ['jpg', 'jpeg', 'bmp']:
        return infile 

    file_size = get_file_size(infile)
    im = Image.open(infile)
    if file_size <= goalkb: 
        return infile

    outfile = IMAGE_COMPRESS_DIR + name + '.' + suffix

    while file_size > goalkb:
        im.save(outfile, quality=quality)
        quality -= step
        file_size = get_file_size(outfile)
        if quality < 60: break

    return outfile

for file_path in sys.argv[1:]:
    if 'http' in file_path:
        # 网页图片
        result = requests.get(file_path, verify=False)
        if result.headers['content-type'].split('/')[0] != 'image':
            print('not valid content-type url:', file_path)
            exit(-1)
        image_type = result.headers['content-type'].split('/')[1]
        file_suffix = ''
        if image_type == 'svg+xml' or image_type == 'svg':
            file_suffix += 'svg'
        elif image_type == 'png':
            file_suffix += 'png'
        elif image_type == 'jpeg':
            file_suffix += 'jpeg'
        elif image_type == 'jpg':
            file_suffix += 'jpg'
        elif image_type == 'gif':
            file_suffix += 'gif'
        elif image_type == 'bmp':
            file_suffix += 'bmp'
        else:
            print('not valid content-type type:', image_type)
            exit(-1)
        # 生成md5
        md5 = hashlib.md5()
        md5.update(result.content)
        md5_code = md5.hexdigest()
        file_name = IMAGE_COPYED_DIR + md5_code + '.' + file_suffix
        open(file_name, 'wb').write(result.content)
        file_path = file_name
    else:
        # 本地图片
        file_content = open(file_path, 'rb').read()
        _, file_suffix = get_file_name_suffix(file_path)
        if file_suffix not in ['jpg','jpeg','png','gif','bmp','svg']:
            print('not valid suffix type:', file_suffix)
            exit(-1)
        md5 = hashlib.md5()
        md5.update(file_content)
        md5_code = md5.hexdigest()
        file_name = IMAGE_COPYED_DIR + md5_code + '.' + file_suffix
        
        open(file_name, 'wb').write(file_content)
        file_path = file_name

    # 尝试压缩图片
    file_path = compress_image(file_path)

    # 上传图片
    headers = {'token': IMAGE_PUT_TOKEN}
    files = {'file':  open(file_path, 'rb')}
    post_result = requests.post(IMAGE_PUT_URL, files=files, headers=headers)

    if '"status":0' in post_result.text and '"upload_result":0' in post_result.text:
        print(IMAGE_GET_URL + '/' + json.loads(post_result.text)['data']['img_name'])
        exit(0) 
    else:
        print('upload failed:' + post_result.text)
        exit(-1) 