
# AI Resume Analyzer

## 1. Project Purpose

The AI Resume Analyzer is a Python-based application that uses a Large Language Model (LLM) to analyze resumes and extract useful candidate information.

The application uses FastAPI to provide an API endpoint and Ollama with the Qwen 2.5 model to process resumes.

The system extracts:

- Candidate name
- Skills
- Work experience
- Education
- Resume score
- Reasoning for the score
- Token usage

## 2. Architecture

The application follows this workflow:

1. User uploads a resume.
2. FastAPI receives the uploaded file.
3. The application validates the file type and size.
4. Text is extracted from the PDF or DOCX file.
5. The extracted text is sent to Ollama.
6. Qwen 2.5 analyzes the resume.
7. The LLM returns structured JSON.
8. FastAPI sends the analysis result to the user.

### Technologies Used

| Technology  | Purpose                   |
| ----------- | ------------------------- |
| Python      | Main programming language |
| FastAPI     | API development           |
| Ollama      | Local LLM execution       |
| Qwen 2.5 7B | Resume analysis           |
| PyPDF       | PDF text extraction       |
| python-docx | DOCX text extraction      |
| Requests    | Ollama API communication  |
| Pytest      | Automated testing         |

## 3. Project Structure

```text
Task3/
│
├── Task3.py
├── test_task3.py
├── evaluate.py
├── .env
├── Resumes/
│
└── Task2/
    ├── README.md
    ├── .env.example
    └── screenshots/
```

## 4. Setup Instructions

### Prerequisites

- Python 3.15
- Ollama
- Qwen 2.5 model

### Install Python Dependencies

Run the following command:

```bash
pip install fastapi uvicorn python-multipart python-dotenv requests pypdf python-docx pytest httpx
```

### Install Ollama Model

Install Ollama and download the model:

```bash
ollama pull qwen2.5:7b
```

Start Ollama before running the application.

## 5. Environment Configuration

Create a `.env` file in the main project folder.

Example:

```env
OLLAMA_URL=http://localhost:11434
MODEL_NAME=qwen2.5:7b
```

The `.env` file contains local configuration and should not be committed to GitHub.

Use `.env.example` as a template.

## 6. Run the Application

Open the terminal in the main `Task3` project folder.

Run:

```bash
uvicorn Task3:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### API Documentation

Open the following URL in your browser:

```text
http://127.0.0.1:8000/docs
```

Swagger UI allows users to test the API by uploading resumes.

## 7. API Endpoints

### Health Check

```http
GET /health
```

Checks whether the application can connect to Ollama.

### Resume Analysis

```http
POST /analyze
```

Accepts PDF and DOCX resume uploads and returns structured analysis.

### Example curl Command

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -F "file=@resume.pdf"
```

### Example Response

```json
{
  "filename": "resume.pdf",
  "analysis": {
    "candidate_name": "John Smith",
    "skills": ["Python", "SQL", "Machine Learning"],
    "experience": ["3 years of experience"],
    "education": ["Bachelor's Degree"],
    "score": 85,
    "reasoning": "Good technical skills",
    "tokens_used": 150
  }
}
```

The example values above are illustrative.

## 8. Testing

Run automated tests using:

```bash
python -m pytest test_task3.py -v
```

The tests cover:

- Successful resume analysis
- Invalid JSON followed by a successful retry
-
