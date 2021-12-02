
## Support only, .jpg, .jpeg, .png, .pdf

# use script from bottom and make requests to  qr-code checker API
# `/QRFile` is a folder with qe-codes* 
```python
import requests
import os
import base64


import logging

logging.basicConfig(level=logging.INFO, filename="logfile.log", filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")

for filename_p in os.listdir('./QRFile/'):
    if not filename_p.endswith('.txt'):
        try:
            with open(f"./QRFile/{filename_p}", "rb") as image_file:
                encoded_string = str(base64.b64encode(image_file.read()))[2:-1]
                d = requests.post('https://pacific-reaches-49119.herokuapp.com/api/v1/base64', json={'base64': encoded_string}, verify=False)
                logging.info(f"{filename_p} + {d.json()}")
        except Exception as e:
            logging.info(e)
```
