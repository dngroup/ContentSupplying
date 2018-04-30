package main

import (
	"log"

	uuid "github.com/satori/go.uuid"
	"github.com/streadway/amqp"
)

func failOnError(err error, msg string) {
	if err != nil {
		log.Fatalf("%s: %s", msg, err)
	}
}

func callCelery(title string) {
	u1 := uuid.NewV4()
	conn, err := amqp.Dial("amqp://guest:guest@localhost:5672/")
	failOnError(err, "Failed to connect to RabbitMQ")
	defer conn.Close()

	ch, err := conn.Channel()
	failOnError(err, "Failed to open a channel")
	defer ch.Close()

	q, err := ch.QueueDeclare(
		"video", // name
		true,    // durable
		false,   // delete when unused
		false,   // exclusive
		false,   // no-wait
		nil,     // arguments
	)
	failOnError(err, "Failed to declare a queue")
	myURL := "localhost"
	body := "{\"id\":\"" + u1.String() + "\",\"task\":\"msstream_worker.msEncoding\",\"args\":[\"" + title + "\",\"" + title + ".mp4\",\"http://" + myURL + "/settings/settings.ini\",\"http://" + myURL + "/rawvideo/" + title + ".mp4\",\"http://" + myURL + "/final/" + title + "\"]}"

	err = ch.Publish(
		"",     // exchange
		q.Name, // routing key
		false,  // mandatory
		false,  // immediate
		amqp.Publishing{
			ContentType: "application/json",
			Body:        []byte(body),
		})
	//log.Printf(" [x] Sent %s", body)
	failOnError(err, "Failed to publish a message")
}

func main() {
	callCelery("NameVideo")
}
