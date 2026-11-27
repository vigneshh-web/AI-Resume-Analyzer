
import json
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from docx import Document

from Task3 import app

client = TestClient(app)


def create_docx():
    document = Document()
    document.add_paragraph("John Smith")
    document.add_paragraph("Python, SQL, Machine Learning")
    document.add_paragraph("3 years of experience")

    file = BytesIO()
    document.save(file)

    return file.getvalue()


def test_successful_resume_analysis():
    mock_response = {
        "candidate_name": "John Smith",
        "skills": ["Python", "SQL", "Machine Learning"],
        "experience": ["3 years of experience"],
        "education": ["Not specified"],
        "score": 85,
        "reasoning": "Good technical skills"
    }

    with patch(
        "Task3.call_ollama",
        return_value=(json.dumps(mock_response), 100)
    ):
        response = client.post(
            "/analyze",
            files={
                "file": (
                    "resume.docx",
                    create_docx(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            }
        )

    assert response.status_code == 200
    assert response.json()["analysis"]["candidate_name"] == "John Smith"
    assert response.json()["analysis"]["score"] == 85


def test_invalid_json_then_success():
    mock_response = {
        "candidate_name": "John Smith",
        "skills": ["Python", "SQL"],
        "experience": ["3 years"],
        "education": ["Not specified"],
        "score": 80,
        "reasoning": "Good resume"
    }

    with patch(
        "Task3.call_ollama",
        side_effect=[
            ("Invalid JSON response", 50),
            (json.dumps(mock_response), 100)
        ]
    ) as mock_llm:

        response = client.post(
            "/analyze",
            files={
                "file": (
                    "resume.docx",
                    create_docx(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            }
        )

    assert response.status_code == 200
    assert mock_llm.call_count == 2
    assert response.json()["analysis"]["tokens_used"] == 150


def test_empty_file():
    response = client.post(
        "/analyze",
        files={
            "file": ("empty.pdf", b"", "application/pdf")
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty"


def test_wrong_file_type():
    response = client.post(
        "/analyze",
        files={
            "file": ("resume.txt", b"Some resume text", "text/plain")
        }
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Only PDF and DOCX files are supported"
