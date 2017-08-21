FROM ubuntu:17.04

RUN apt-get update -y

# dependencies
RUN apt install libmediainfo-dev -y
RUN apt install curl -y

# ffmpeg
RUN apt install ffmpeg -y

#gpac
RUN apt install gpac -y

# node
RUN curl -o /usr/local/bin/n https://raw.githubusercontent.com/visionmedia/n/master/bin/n
RUN chmod +x /usr/local/bin/n
RUN n stable


ADD . /encoding
WORKDIR /encoding

ENTRYPOINT ["node", "src/index.js"]