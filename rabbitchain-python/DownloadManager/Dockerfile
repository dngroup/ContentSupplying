FROM python:2.7.12-alpine
MAINTAINER mlacaud@viotech.net

RUN apk add --no-cache ca-certificates
RUN pip install requests
RUN pip install jsonpickle
RUN pip install pafy

ADD download.py download.py
ADD entrypoint.sh entrypoint.sh
RUN chmod 755 entrypoint.sh

CMD ./entrypoint.sh