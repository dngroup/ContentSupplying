FROM python:2.7-alpine
MAINTAINER mlacaud@viotech.net

RUN apk add --no-cache ffmpeg
RUN pip install Celery
RUN pip install pymediainfo

ADD . .
RUN chmod 755 entrypoint.sh

CMD ./entrypoint.sh
