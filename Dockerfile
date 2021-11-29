# set base image (host OS)
FROM python:3.7

# set the working directory in the container
WORKDIR /app

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN apt-get update
RUN apt-get install -y libzbar0
RUN pip3 install -r requirements.txt
COPY . .

EXPOSE 80
CMD ["gunicorn", "--workers", "5", "--max-requests", "300", "--bind", "0.0.0.0:$PORT", "--preload", "--log-level", "debug", "wsgi:app"]
