import os
from flask import Flask, jsonify, make_response, render_template, request, flash, redirect, url_for
import cv2
import fitz
from pyzbar.pyzbar import decode
import requests
from fake_headers import Headers
import base64
import numpy as np

header = Headers(headers=True).generate()

app = Flask(__name__)

UPLOAD_FOLDER = './tmp'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super secret key'

extensons_img = ['.jpg', '.png', '.jpeg']

if not os.path.exists('./tmp'):
    os.makedirs('./tmp')


def second_method(img_path):
    data_src = decode(cv2.imread(img_path))
    link = str(data_src[0][0]).replace("b'", '').replace("'", '')
    return {'decoded_url': link}


def proces_path(path):
    try:
        img = cv2.imread(path)
        decoder = cv2.QRCodeDetector()
        data, points, _ = decoder.detectAndDecode(img)
        if points is not None:
            return {'decoded_url': data}
    except Exception as e:
        return {'error': e}


def convert_pdf_to_images(pdf_path):
    file_name = pdf_path.split('/')[-1]
    pdffile = pdf_path
    doc = fitz.open(pdffile)
    for i in range(doc.page_count - 1):
        page = doc.load_page(i)  # number of page
        pix = page.get_pixmap()
        output = fr"./tmp/{file_name} - {i}.png"
        pix.save(output)
        data = proces_path(output)
        if data['decoded_url']:
            api_gos = 'https://www.gosuslugi.ru/api/covid-cert/v3/cert/check/' + data['decoded_url'].split('/')[-1]
            is_valid = requests.get(url=api_gos, headers=header, verify=False).json()
            data['status'] = is_valid['items'][0]['status']
            data['expires_at'] = is_valid['items'][0]['expiredAt']
            return data
        else:
            data = second_method(output)
            if data['decoded_url']:
                try:
                    api_gos = 'https://www.gosuslugi.ru/api/covid-cert/v3/cert/check/' + data['decoded_url'].split('/')[-1]
                    is_valid = requests.get(url=api_gos, headers=header, verify=False).json()
                    data['status'] = is_valid[0]['items']['status']
                    data['expires_at'] = is_valid['items'][0]['expiredAt']
                    return data
                except:
                    return data
        return {'error': 'unreadable pdf'}


def get_qr(path_to_file):
    is_img = False
    for ext in extensons_img:
        if path_to_file.endswith(ext):
            is_img = True
    else:
        if_pdf = True
    if is_img:
        data = proces_path(path_to_file)
        if data['decoded_url']:
            try:
                api_gos = 'https://www.gosuslugi.ru/api/covid-cert/v3/cert/check/' + data['decoded_url'].split('/')[-1]
                is_valid = requests.get(url=api_gos, headers=header, verify=False).json()
                data['status'] = is_valid['items'][0]['status']
                data['expires_at'] = is_valid['items'][0]['expiredAt']
                return data
            except:
                return data
        else:
            data = second_method(path_to_file)
            if data['decoded_url']:
                try:
                    api_gos = 'https://www.gosuslugi.ru/api/covid-cert/v3/cert/check/' + data['decoded_url'].split('/')[-1]
                    is_valid = requests.get(url=api_gos, headers=header, verify=False).json()
                    data['status'] = is_valid[0]['status']
                    data['expires_at'] = is_valid[0]['expiredAt']
                    return data
                except:
                    return data
        return {'error': 'unreadable img'}
    elif if_pdf:
        return convert_pdf_to_images(path_to_file)


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response


def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route("/health", methods=['GET'])
def health():
    return jsonify({'status': 'OK'})


@app.route("/", methods=['GET'])
def home_qr():
    return render_template('index.html')


@app.route('/api/v1/ui', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(f"./tmp/{f.filename}")
        data = get_qr(f"./tmp/{f.filename}")
        for filename in os.listdir('./tmp'):
            if f.filename in filename:
                os.remove(f"./tmp/{filename}")
        return jsonify(data)


@app.route('/api/v1/base64', methods=['GET', 'POST'])
def upload_base():
    if request.method == 'POST':
        tmpname = np.random.randint(1, 1000000)
        f = request.json.get('base64')
        ext = None
        if f[0] == 'i':
            ext = 'png'
        if f[0] == '/':
            ext = 'jpg'
        if f[0] == 'J':
            ext = 'pdf'
        if ext:
            filename_tmp = f"{tmpname}.{ext}"
            with open(f"./tmp/{filename_tmp}", "wb") as fh:
                fh.write(base64.b64decode(f))
                fh.close()
            data = get_qr(f"./tmp/{filename_tmp}")
            for filename_p in os.listdir('./tmp'):
                if filename_tmp in filename_p:
                    os.remove(f"./tmp/{filename_p}")
            return jsonify(data)


if __name__ == '__main__':
    app.run(host="0.0.0.0")
