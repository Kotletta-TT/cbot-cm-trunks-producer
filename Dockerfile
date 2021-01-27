FROM python:3

WORKDIR /usr/src/app

ENV RABBIT_HOST=172.20.0.1
ENV RABBIT_QUEUE=hello
ENV LOG_LEVEL=WARNING
ENV TIMEOUT_REQUEST=5

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


CMD ["python", "./main.py"]