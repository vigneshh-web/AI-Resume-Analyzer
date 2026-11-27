
# AI Resume Analyzer – 5-Minute Demo

## 1. Introduction

This project is an AI-powered Resume Analyzer built using Python, FastAPI, and Ollama with the Qwen 2.5 model.

## 2. Successful Resume Analysis

- Open the API documentation at http://127.0.0.1:8000/docs.
- Select the POST /analyze endpoint.
- Upload a PDF or DOCX resume.
- Execute the request.
- Show the structured JSON output, extracted skills, score, and reasoning.

## 3. Failure Case

- Upload an unsupported TXT file.
- Show the HTTP 415 response.
- Explain that the API accepts only PDF and DOCX files.

## 4. Conclusion

The project demonstrates resume text extraction, LLM-based analysis, API development, input validation, and error handling.

## 5. Limitations

AI-generated results may contain mistakes. Human review is necessary before making recruitment decisions.
