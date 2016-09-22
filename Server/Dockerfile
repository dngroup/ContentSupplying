FROM golang:1.6.3-alpine
MAINTAINER mlacaud@viotech.net

RUN apk add --no-cache git
RUN apk add --no-cache unzip
RUN go get github.com/gorilla/mux

ADD ContentSupplying.go ContentSupplying.go

CMD go run ContentSupplying.go