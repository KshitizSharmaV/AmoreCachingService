FROM python:3.9
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git
WORKDIR /code
COPY requirements.txt /code
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . /code
EXPOSE 5050
ENTRYPOINT gunicorn app:app -b 0.0.0.0:5050