FROM python:3.8-slim
WORKDIR /app
ENV PYTHONPATH /app

RUN apt-get update && apt-get install -y libsecp256k1-0 build-essential git

COPY requirements.txt .
RUN pip install python-bitcointx
RUN pip install git+https://gitlab.com/thorchain/bifrost/python-dogecointx.git#egg=python-dogecointx
RUN pip install -r requirements.txt

COPY . .
