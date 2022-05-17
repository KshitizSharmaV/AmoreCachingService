FROM python:3.9
WORKDIR /code
COPY requirements.txt /code
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . /code
WORKDIR /code/ProximityHash
RUN python setup.py install
WORKDIR /code
EXPOSE 5050
ENTRYPOINT gunicorn app:app -b 0.0.0.0:5050