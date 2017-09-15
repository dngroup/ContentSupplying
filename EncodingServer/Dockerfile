FROM ubuntu:16.04

RUN apt-get update -y

# dependencies
RUN apt-get install libmediainfo-dev -y
RUN apt-get install curl -y

# ffmpeg
RUN apt-get install ffmpeg -y

#gpac
RUN apt-get install gpac -y

RUN apt-get install make -y

RUN apt-get install g++ -y

RUN apt-get install gcc -y
# node
#RUN curl -o /usr/local/bin/n https://raw.githubusercontent.com/visionmedia/n/master/bin/n
#RUN chmod +x /usr/local/bin/n
#RUN n stable

RUN curl -sL https://deb.nodesource.com/setup_8.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get install nodejs -y

ADD . /encoding
WORKDIR /encoding

RUN npm install

ENTRYPOINT ["node", "src/index.js"]