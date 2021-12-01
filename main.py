import os
from flask import Flask, jsonify, make_response, render_template, request
import cv2
import fitz
from pyzbar.pyzbar import decode
from pdf2image import convert_from_path
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
    try:
        data_src = decode(cv2.imread(img_path))
        link = str(data_src[0][0]).replace("b'", '').replace("'", '')
        return {'decoded_url': link}

    except Exception as e:
        return {'error': e,
                'decoded_url': ''}


def third_method(path_to_pdf):
    try:
        image = convert_from_path(path_to_pdf)[0]
        data_src = decode(image)
        link = str(data_src[0][0]).replace("b'", '').replace("'", '')
        return {'decoded_url': link}

    except Exception as e:
        return {'error': e,
                'decoded_url': ''}

def proces_path(path):
    try:
        img = cv2.imread(path)
        decoder = cv2.QRCodeDetector()
        data, points, _ = decoder.detectAndDecode(img)
        if points is not None:
            return {'decoded_url': data}
        else:
            return {'decoded_url': ''}
    except Exception as e:
        return {'error': e,
                'decoded_url': ''}


def pdf_process(output):
    data = proces_path(output)
    if data['decoded_url']:
        api_gos = 'https://www.gosuslugi.ru/api/covid-cert/v3/cert/check/' + data['decoded_url'].split('/')[-1]
        is_valid = requests.get(url=api_gos, headers=header, verify=False)
        if is_valid.status_code == 200:
            is_valid = is_valid.json()
            data['status'] = is_valid['items'][0]['status']
            data['expires_at'] = is_valid['items'][0]['expiredAt']
            return data
        return data
    else:
        data = second_method(output)
        if data['decoded_url']:
            api_gos = 'https://www.gosuslugi.ru/api/covid-cert/v3/cert/check/' + data['decoded_url'].split('/')[-1]
            is_valid = requests.get(url=api_gos, headers=header, verify=False)
            if is_valid.status_code == 200:
                is_valid = is_valid.json()
                data['status'] = is_valid['items'][0]['status']
                data['expires_at'] = is_valid['items'][0]['expiredAt']
                return data
        else:
            data = third_method(output.split(' -')[0])
            if data['decoded_url']:
                api_gos = 'https://www.gosuslugi.ru/api/covid-cert/v3/cert/check/' + data['decoded_url'].split('/')[-1]
                is_valid = requests.get(url=api_gos, headers=header, verify=False)
                if is_valid.status_code == 200:
                    is_valid = is_valid.json()
                    data['status'] = is_valid['items'][0]['status']
                    data['expires_at'] = is_valid['items'][0]['expiredAt']
                    return data
                return data
    return {'error': 'unreadable pdf', 'decoded_url': ''}


def convert_pdf_to_images(pdf_path):
    file_name = pdf_path.split('/')[-1]
    pdffile = pdf_path
    doc = fitz.open(pdffile)
    rg = 0
    if doc.page_count > 1:
        rg = doc.page_count - 1
    if rg == 0:
        page = doc.load_page(rg)  # number of page
        pix = page.get_pixmap()
        output = fr"./tmp/{file_name} - {rg}.png"
        pix.save(output)
        data = pdf_process(output)
        return data
    for i in range(doc.page_count - 1):
        page = doc.load_page(i)  # number of page
        pix = page.get_pixmap()
        output = fr"./tmp/{file_name} - {i}.png"
        pix.save(output)
        data = pdf_process(output)
        return data


def get_qr(path_to_file):
    try:
        is_img = False
        for ext in extensons_img:
            if path_to_file.endswith(ext):
                is_img = True
        else:
            if_pdf = True
        if is_img:
            data = proces_path(path_to_file)
            if data['decoded_url']:
                api_gos = 'https://www.gosuslugi.ru/api/covid-cert/v3/cert/check/' + data['decoded_url'].split('/')[-1]
                is_valid = requests.get(url=api_gos, headers=header, verify=False)
                if is_valid.status_code == 200:
                    is_valid = is_valid.json()
                    data['status'] = is_valid['items'][0]['status']
                    data['expires_at'] = is_valid['items'][0]['expiredAt']
                    return data
                return data
            else:
                data = second_method(path_to_file)
                if data['decoded_url']:
                    api_gos = 'https://www.gosuslugi.ru/api/covid-cert/v3/cert/check/' + data['decoded_url'].split('/')[
                        -1]
                    is_valid = requests.get(url=api_gos, headers=header, verify=False)
                    if is_valid.status_code == 200:
                        is_valid = is_valid.json()
                        data['status'] = is_valid['items'][0]['status']
                        data['expires_at'] = is_valid['items'][0]['expiredAt']
                        return data
                    return data
            return {'error': 'unreadable img', 'decoded_url': ''}
        elif if_pdf:
            return convert_pdf_to_images(path_to_file)
        else:
            return {'error': 'unsupportable file', 'decoded_url': ''}
    except Exception as e:
        return {'error': e, 'decoded_url': ''}


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
        f.save(fr"./tmp/{f.filename}")
        data = get_qr(fr"./tmp/{f.filename}")
        for filename in os.listdir('./tmp'):
            if f.filename in filename:
                try:
                    os.remove(fr"./tmp/{filename}")
                except Exception as e:
                    print(e)
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
            with open(fr"./tmp/{filename_tmp}", "wb") as fh:
                fh.write(base64.b64decode(f))
                fh.close()
            data = get_qr(fr"./tmp/{filename_tmp}")
            for filename_p in os.listdir('./tmp'):
                if filename_tmp in filename_p:
                    try:
                        os.remove(fr"./tmp/{filename_tmp}")
                    except Exception as e:
                        print(e)
            return jsonify(data)


if __name__ == '__main__':
    app.run(host="0.0.0.0")
