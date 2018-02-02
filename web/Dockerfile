FROM python:3.5-alpine
RUN apk update && \
    apk add bash && \
    apk add --virtual build-deps gcc python3-dev musl-dev && \
    apk add postgresql-dev && \
    apk del build-deps
COPY . /web
WORKDIR /web
RUN pip install -r requirements.txt
ENTRYPOINT ["./run.sh"]