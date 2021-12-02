# set base image (host OS)
FROM python:3.7

RUN apt-get clean \
    && apt-get -y update

RUN apt-get -y install \
    poppler-utils\
    libzbar-dev \
    libzbar0

WORKDIR /app

# copy the dependencies file to the working directory
COPY requirements.txt .


RUN pip3 install -r requirements.txt
COPY . .

EXPOSE 80
CMD ["gunicorn", "--workers", "10", "--max-requests", "10000", "--worker-connections", "--preload", "--log-level", "debug", "wsgi:app"]
