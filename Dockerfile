# syntax=docker/dockerfile:1
FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt ./

RUN apk add --no-cache gcc musl-dev linux-headers

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python","-u","friendme.py"]