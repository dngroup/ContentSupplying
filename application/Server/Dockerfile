FROM golang

RUN apt update -y && apt install -y unzip

RUN go get -u github.com/jinzhu/gorm
RUN go get github.com/go-sql-driver/mysql
RUN go get github.com/gorilla/mux
RUN go get github.com/gorilla/handlers
RUN go get github.com/satori/go.uuid
RUN go get github.com/streadway/amqp


RUN mkdir filesServer

COPY . ./app

WORKDIR app

CMD ./wait-for-it.sh db:3306 && go run main.go -b broker:5672 -a server -d db:3306
