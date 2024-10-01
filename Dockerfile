FROM python:3.12-alpine
WORKDIR /app
COPY ./requirements.txt /requirements.txt
RUN python -m pip install -r /requirements.txt
RUN mkdir /scratch
