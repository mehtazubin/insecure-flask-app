FROM python:3.5-alpine
RUN apk update && \
    apk add bash && \
    apk add --virtual build-deps && \
    apk add gcc python3-dev musl-dev && \
    apk add postgresql-dev && \
    apk del build-deps
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /web
WORKDIR /web
RUN chmod a+x run.sh
ENTRYPOINT ["./run.sh"]