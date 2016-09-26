FROM python:3.5.2-alpine
MAINTAINER mlacaud@viotech.net

RUN apk add --no-cache ffmpeg

RUN pip install Celery
RUN pip install pymediainfo
ADD /usr/bin/MP4Box /usr/bin/MP4Box
ADD . .
RUN chmod 755 entrypoint.sh

CMD ./entrypoint.sh
