package main

import (
	"fmt"
	"html/template"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/gorilla/handlers"
	"github.com/gorilla/mux"
)

// Struct for the result page data
type ResultPageData struct {
	Result     string
	Confidence string
	IsFake     bool
}

func main() {
	r := mux.NewRouter()

	// Endpoint to handle file upload
	r.HandleFunc("/upload", uploadFileHandler).Methods("POST")

	// Serve the static frontend HTML
	r.PathPrefix("/").Handler(http.StripPrefix("/", http.FileServer(http.Dir("./static/"))))

	// CORS support
	headersOk := handlers.AllowedHeaders([]string{"X-Requested-With", "Content-Type", "Authorization"})
	originsOk := handlers.AllowedOrigins([]string{"*"})
	methodsOk := handlers.AllowedMethods([]string{"GET", "HEAD", "POST", "OPTIONS"})

	// Start the server
	port := ":8080"
	log.Printf("Starting server on %s\n", port)
	log.Fatal(http.ListenAndServe(port, handlers.CORS(originsOk, headersOk, methodsOk)(r)))
}

// Handle file upload
func uploadFileHandler(w http.ResponseWriter, r *http.Request) {
	// Parse the uploaded file
	err := r.ParseMultipartForm(10 << 20) // Max file size: 10 MB
	if err != nil {
		log.Printf("Error parsing form: %v", err)
		http.Error(w, "Error parsing form", http.StatusBadRequest)
		return
	}

	// Get the file from the request
	file, handler, err := r.FormFile("file")
	if err != nil {
		log.Printf("Error retrieving file: %v", err)
		http.Error(w, "Error retrieving file", http.StatusInternalServerError)
		return
	}
	defer file.Close()

	// Create the uploads directory if it doesn't exist
	err = os.MkdirAll("uploads", os.ModePerm)
	if err != nil {
		log.Printf("Error creating uploads directory: %v", err)
		http.Error(w, "Error creating uploads directory", http.StatusInternalServerError)
		return
	}

	// Save the file locally
	filePath := filepath.Join("uploads", handler.Filename)
	f, err := os.Create(filePath)
	if err != nil {
		log.Printf("Error saving file: %v", err)
		http.Error(w, "Error saving file", http.StatusInternalServerError)
		return
	}
	defer f.Close()
	io.Copy(f, file)

	// Run deepfake detection (assume a Python model is used)
	detectionResult, confidence, isFake, err := runDeepfakeDetection(filePath)
	if err != nil {
		log.Printf("Error running deepfake detection: %v", err)
		http.Error(w, fmt.Sprintf("Error processing video: %v", err), http.StatusInternalServerError)
		return
	}

	// Render the result page
	renderResultPage(w, detectionResult, confidence, isFake)
}

// Function to run deepfake detection using Python
func runDeepfakeDetection(videoPath string) (string, string, bool, error) {
	// Execute the Python script with the video file path as an argument
	cmd := exec.Command("python", "python_script.py", videoPath)
	output, err := cmd.CombinedOutput() // Capture both stdout and stderr
	if err != nil {
		return "", "", false, fmt.Errorf("error running deepfake detection: %v - output: %s", err, output)
	}

	// Parse the output (assumes your script prints the result and confidence)
	// You may need to adjust this part depending on how you format the output in your Python script.
	var result string
	var confidence float64
	if string(output) == "real" {
		result = "The video is classified as Fake"
		return result, fmt.Sprintf("%.2f", confidence), false, nil
	} else {
		result = "The video is classified as Real"
		return result, fmt.Sprintf("%.2f", confidence), true, nil
	}
}

// Function to render the result page
func renderResultPage(w http.ResponseWriter, resultMessage string, confidence string, isFake bool) {
	data := ResultPageData{
		Result:     resultMessage,
		Confidence: confidence,
		IsFake:     isFake,
	}
	tmpl, err := template.ParseFiles("static/result.html")
	if err != nil {
		http.Error(w, "Error loading template", http.StatusInternalServerError)
		return
	}
	tmpl.Execute(w, data)
}
