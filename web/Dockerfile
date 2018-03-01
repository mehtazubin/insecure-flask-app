FROM python:3.5-alpine
RUN apk update && \
    apk add bash && \
    apk add --virtual build-deps && \
    apk add gcc python3-dev musl-dev jpeg-dev && \
    apk add postgresql-dev git && \
    apk del build-deps
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN (stat /tmp/Flask-Images || git clone --depth 1 https://github.com/wzuo/Flask-Images /tmp/Flask-Images) && pip install -e /tmp/Flask-Images
COPY . /web
WORKDIR /web
RUN chmod a+x run.sh && \
    mkdir /web/static/images
ENTRYPOINT ["./run.sh"]