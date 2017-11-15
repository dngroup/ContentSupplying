package main

import (
	"net/http"
	"github.com/gorilla/mux"
	"github.com/gorilla/handlers"
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
	"github.com/jinzhu/gorm"
    	_ "github.com/jinzhu/gorm/dialects/mysql"
)
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//
// Var and Struct
//
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
var rootPath string
var myUrl string
var brokerUrl string
var db *gorm.DB
var myPort string
var dbaddr string

type Data struct {
	ID   uint `gorm:"primary_key"`
	Uuid string
	Name string
	IsReady int
	Link string
}

type DataList struct {
	Datas []Data
}

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

func callCelery(title string, u1 string){
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

        body := "{\"id\":\"" + u1 + "\",\"task\":\"msstream_worker.msEncoding\",\"args\":[\""+title+"\",\"http://"+myUrl+ ":" + myPort + "/settings/settings.ini\",\"http://"+myUrl+ ":"+myPort+"/zip/"+title+".zip\",\"http://"+myUrl+":"+myPort+"/final/"+title+"\"]}"
	//fmt.Println(body)
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
	//err := exec.Command("7z","x",path,"-y","-o"+outpath, "-r").Run()
	if err != nil {
		fmt.Fprintln(os.Stdout, err)
	}

	/*err2 := exec.Command("chmod","755","-R",outpath).Run()

	if err2 != nil {
		fmt.Fprintln(os.Stdout, err)
	}*/
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
	case "GET":
		var u []Data
		db.Find(&u)

		res.Header().Set("Content-Type", "application/json; charset=UTF-8")
		json.NewEncoder(res).Encode(&u)
		break
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
		break
	}
}

func handleRawContent(res http.ResponseWriter, req *http.Request) {
	vars := mux.Vars(req)
	ytb_id := vars["ytb_id"]

	switch req.Method {
	case "POST":
		uuid_fin := uuid.NewV4().String()
		db.Create(&Data{Uuid: uuid_fin,IsReady: 0, Name: ytb_id, Link: "superlink"})
		f, handler, _ := req.FormFile("trailer")
		fmt.Println(handler.Filename)
		superfile := rootPath + "zip/" +  handler.Filename
		// Create the file
		out, err := os.Create(superfile)
		if err != nil  {
			http.Error(res, err.Error(), http.StatusInternalServerError)
			return
		}
		defer out.Close()
		// Copy
		_, err = io.Copy(out, f)
		if err != nil  {
			http.Error(res, err.Error(), http.StatusInternalServerError)
			return
		}
		//callCelery(ytb_id, uuid_fin)
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
		var u Data
		db.Last(&u, "name = ?", ytb_id)
		u.IsReady = 1
		db.Save(&u)
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
		uuid_fin := uuid.NewV4().String()
		callCelery(ytb_id, uuid_fin)
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
	var err error
	// Cli
	flag.StringVar(&rootPath, "f","./filesServer/","path of the folder containing the contents, ending with '/'")
	flag.StringVar(&myUrl, "a","localhost","public address of the current server")
	flag.StringVar(&brokerUrl, "b","localhost:5672","Url of the rabbitMQ broker")
	flag.StringVar(&myPort, "p", "8085", "Port of the server")
	flag.StringVar(&dbaddr, "d", "localhost:3306", "Address and port of the database")
	flag.Parse()

	// Folder management
	os.MkdirAll(rootPath + "zip/", 0755)
	os.MkdirAll(rootPath + "finalzip/", 0755)
	os.MkdirAll(rootPath + "finalContent/", 0755)

	db, err = gorm.Open("mysql", "re355:re355@tcp(" + dbaddr + ")/re355")
	if err != nil {
    		log.Fatal(err)
	}
	defer db.Close()

	db.AutoMigrate(&Data{})

	//db.Create(&Data{Name: "coucou"})

	// Server creation
	router := mux.NewRouter()

	settings := http.StripPrefix("/settings", http.FileServer(http.Dir("./settings/")))
    	router.PathPrefix("/settings/").Handler(settings)
	s := http.StripPrefix("/zip/", http.FileServer(http.Dir(rootPath + "/zip/")))
    	router.PathPrefix("/zip/").Handler(s)
	staticVid := http.StripPrefix("/video/", http.FileServer(http.Dir(rootPath + "/finalContent/")))
    	router.PathPrefix("/video/").Handler(staticVid)
	router.HandleFunc("/content", handleContent).Methods("GET", "POST")
	router.HandleFunc("/content/{ytb_id}", handleRawContent).Methods("POST")
	router.HandleFunc("/final/{ytb_id}", handleFinalContentCall).Methods("POST")
	router.HandleFunc("/celery/{ytb_id}", handleCeleryCall).Methods("POST")
	log.Printf("Listening at http://0.0.0.0:%s", myPort)
	log.Fatal(http.ListenAndServe(":" + myPort, handlers.CORS()(router)))
}
