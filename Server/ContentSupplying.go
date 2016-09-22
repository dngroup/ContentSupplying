package main

import (
	"net/http"
	"github.com/gorilla/mux"
	"encoding/json"
	"log"
	"fmt"
	"io/ioutil"
	"os"
	"io"
	"github.com/satori/go.uuid"
	"github.com/streadway/amqp"
	"os/exec"
	"flag"
	"strings"
)
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//
// Var and Struct
//
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
var rootPath string
var myUrl string
var brokerUrl string

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//
// Functions
//
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


func readDirectory(path string) []string{
	var out []string
	file, _ := ioutil.ReadDir(path)
	for _, f := range file {
		out = append(out, strings.Replace(f.Name(), ".zip", "", 1))
	}
	return out;
}

func deleteExisting(slice1 []string, slice2 []string) ([]string){
	diffStr := []string{}
	m :=map [string]int{}

	for _, s1Val := range slice1 {
		m[s1Val] = 1
	}
	for _, s2Val := range slice2 {
		if m[s2Val]==1 {
			m[s2Val] = m[s2Val] + 1
		}
	}

	for mKey, mVal := range m {
		if mVal==1 {
			diffStr = append(diffStr, mKey)
		}
	}

	return diffStr
}

func failOnError(err error, msg string) {
        if err != nil {
                log.Fatalf("%s: %s", msg, err)
        }
}

func callCelery(title string){
	u1 := uuid.NewV4()
        conn, err := amqp.Dial("amqp://guest:guest@"+brokerUrl+"/")
        failOnError(err, "Failed to connect to RabbitMQ")
        defer conn.Close()

        ch, err := conn.Channel()
        failOnError(err, "Failed to open a channel")
        defer ch.Close()

        q, err := ch.QueueDeclare(
                "celery", // name
                true,     // durable
                false,    // delete when unused
                false,    // exclusive
                false,    // no-wait
                nil,      // arguments
        )
        failOnError(err, "Failed to declare a queue")

        body := "{\"id\":\"" + u1.String() + "\",\"task\":\"worker.msEncoding\",\"args\":["+title+",http://"+myUrl+"/zip/"+title+".zip,http://"+myUrl+"/final/"+title+"]}"

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


func unzip(path, outpath string){
	err := exec.Command("unzip",path,"-d",outpath).Run()

	if err != nil {
		fmt.Fprintln(os.Stdout, err)
	}
}












////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//
// Handlers
//
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
func handleContent(res http.ResponseWriter, req *http.Request) {
	res.Header().Set("Content-Type", "application/json")
	var inputList []string;
	var middleList []string;
	var outputList []string;
	switch req.Method {
	case "POST":
		decoder := json.NewDecoder(req.Body)
		error := decoder.Decode(&inputList)
		if error != nil {
			log.Println(error.Error())
			http.Error(res, error.Error(), http.StatusInternalServerError)
			return
		}

		middleList = readDirectory(rootPath + "zip/")

		outputList = deleteExisting(inputList, middleList)

		outgoingJSON, err := json.Marshal(&outputList)
		if err != nil {
			log.Println(error.Error())
			http.Error(res, err.Error(), http.StatusInternalServerError)
			return
		}
		res.WriteHeader(http.StatusCreated)
		fmt.Fprint(res, string(outgoingJSON))
	}
}

func handleRawContent(res http.ResponseWriter, req *http.Request) {
	vars := mux.Vars(req)
	ytb_id := vars["ytb_id"]

	switch req.Method {
	case "POST":
		superfile := rootPath + "zip/" + ytb_id + ".zip"
		// Create the file
		out, err := os.Create(superfile)
		if err != nil  {
			http.Error(res, err.Error(), http.StatusInternalServerError)
			return
		}
		defer out.Close()
		// Copy
		_, err = io.Copy(out, req.Body)
		if err != nil  {
			http.Error(res, err.Error(), http.StatusInternalServerError)
			return
		}

		// Return success
		res.WriteHeader(http.StatusCreated)
		fmt.Fprint(res)
	}
}

func handleFinalContentCall(res http.ResponseWriter, req *http.Request) {
	vars := mux.Vars(req)
	ytb_id := vars["ytb_id"]

	switch req.Method {
	case "POST":
		superfile := rootPath + "finalzip/" + ytb_id + ".zip"
		// Create the file
		out, err := os.Create(superfile)
		if err != nil  {
			http.Error(res, err.Error(), http.StatusInternalServerError)
			return
		}
		defer out.Close()
		// Copy
		_, err = io.Copy(out, req.Body)
		if err != nil  {
			http.Error(res, err.Error(), http.StatusInternalServerError)
			return
		}

		unzip(superfile, rootPath + "finalContent/")

		// Return success
		res.WriteHeader(http.StatusCreated)
		fmt.Fprint(res)
	}
}

func handleCeleryCall(res http.ResponseWriter, req *http.Request) {
	vars := mux.Vars(req)
	ytb_id := vars["ytb_id"]
	switch req.Method {
	case "POST":
		callCelery(ytb_id)
		res.WriteHeader(http.StatusAccepted)
		fmt.Fprint(res)
	}
}











////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//
// Main
//
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
func main() {
	// Cli
	flag.StringVar(&rootPath, "f","../filesServer/","path of the folder containing the contents, ending with '/'")
	flag.StringVar(&myUrl, "a","localhost:8085","public address and port of the current server")
	flag.StringVar(&brokerUrl, "b","localhost:5672","Url of the rabbitMQ broker")
	flag.Parse()

	// Folder management
	os.MkdirAll(rootPath + "zip/", 0755)
	os.MkdirAll(rootPath + "finalzip/", 0755)
	os.MkdirAll(rootPath + "finalContent/", 0755)

	// Server creation
	router := mux.NewRouter()
	s := http.StripPrefix("/zip/", http.FileServer(http.Dir(rootPath + "/zip/")))
    	router.PathPrefix("/zip/").Handler(s)
	router.HandleFunc("/content", handleContent).Methods("POST")
	router.HandleFunc("/content/{ytb_id}", handleRawContent).Methods("POST")
	router.HandleFunc("/final/{ytb_id}", handleFinalContentCall).Methods("POST")
	router.HandleFunc("/celery/{ytb_id}", handleCeleryCall).Methods("POST")
	log.Fatal(http.ListenAndServe(":8085", router))
}