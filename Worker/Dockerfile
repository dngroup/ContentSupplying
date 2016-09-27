FROM ubuntu:16.04
MAINTAINER mlacaud@viotech.net

RUN apt-get update -y

RUN apt-get install libmediainfo-dev -y
RUN apt-get install ffmpeg -y
RUN apt-get install gpac -y
RUN apt-get install python3 -y
RUN apt-get install python3-setuptools -y
RUN apt-get install python3-pip -y

RUN pip3 install Celery
RUN pip3 install configparser
RUN pip3 install pymediainfo
RUN pip3 install requests
RUN pip3 install jsonpickle
ADD . .
RUN chmod 755 entrypoint.sh

CMD ./entrypoint.sh
