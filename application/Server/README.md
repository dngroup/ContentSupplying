# Server

## Dependencies

* Unzip :

```
apt update -y && apt install -y unzip
```

* Go dependecies :

```
go get github.com/jinzhu/gorm
go get github.com/gorilla/mux
go get github.com/gorilla/handlers
go get github.com/satori/go.uuid
go get github.com/streadway/amqp
```

* Run the app:
```
go run main.go -b <broker_addr> -a <ip_address_of_the_computer>
```

**broker_addr** should be like: **localhost:5672**
