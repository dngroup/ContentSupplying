FROM golang:1.6.3-alpine
MAINTAINER mlacaud@viotech.net

RUN apk add --no-cache git
RUN apk add --no-cache unzip
RUN go get github.com/gorilla/mux
RUN go get github.com/satori/go.uuid
RUN go get github.com/streadway/amqp

ADD settings/ settings/
ADD ContentSupplying.go ContentSupplying.go

CMD go run ContentSupplying.go