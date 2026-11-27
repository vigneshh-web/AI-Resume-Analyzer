
import os
import json
import re
import requests

from io import BytesIO
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from pypdf import PdfReader
from docx import Document


load_dotenv()

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "qwen2.5:7b"
)

MAX_FILE_SIZE = 10 * 1024 * 1024

app = FastAPI(
    title="AI Resume Analyzer",
    description="Resume analysis API using Ollama",
    version="1.0"
)


def extract_text(file_bytes, filename):

    extension = os.path.splitext(filename)[1].lower()

    if extension == ".pdf":

        reader = PdfReader(BytesIO(file_bytes))

        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        if not text.strip():
            raise ValueError("No text found in resume")

        return text

    elif extension == ".docx":

        document = Document(BytesIO(file_bytes))

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

        if not text.strip():
            raise ValueError("No text found in resume")

        return text

    elif extension == ".txt":

        text = file_bytes.decode("utf-8")

        if not text.strip():
            raise ValueError("No text found in resume")

        return text

    else:
        raise ValueError("Unsupported file type")


def call_ollama(prompt):

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "num_predict": 1024
        }
    }

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        timeout=(10, 600)
    )

    response.raise_for_status()

    data = response.json()

    tokens_used = (
        data.get("prompt_eval_count", 0)
        + data.get("eval_count", 0)
    )

    return data.get("response", ""), tokens_used


def clean_json_response(response_text):

    if isinstance(response_text, dict):
        return response_text

    if not isinstance(response_text, str):
        raise ValueError("Invalid response format")

    response_text = response_text.strip()

    response_text = re.sub(
        r"^```(?:json)?\s*",
        "",
        response_text
    )

    response_text = re.sub(
        r"\s*```$",
        "",
        response_text
    )

    return json.loads(response_text)


def validate_result(result):

    if not isinstance(result, dict):
        raise ValueError("Response must be a JSON object")

    required_fields = [
        "candidate_name",
        "skills",
        "experience",
        "education",
        "score",
        "reasoning"
    ]

    for field in required_fields:

        if field not in result:
            raise ValueError(f"Missing field: {field}")

    if not isinstance(result["skills"], list):
        raise ValueError("Skills must be a list")

    if not isinstance(result["experience"], list):
        raise ValueError("Experience must be a list")

    if not isinstance(result["education"], list):
        raise ValueError("Education must be a list")

    if not isinstance(result["score"], (int, float)):
        raise ValueError("Score must be numeric")

    if not 0 <= result["score"] <= 100:
        raise ValueError("Score must be between 0 and 100")

    result["skills"] = list(dict.fromkeys(
        skill.strip()
        for skill in result["skills"]
        if isinstance(skill, str) and skill.strip()
    ))

    return result


def analyze_resume(resume_text, prompt_version="improved"):

    if prompt_version == "original":

        prompt = f"""
You are an AI resume analyzer.

Analyze the following resume and extract the candidate's information.

Extract:
1. Candidate name.
2. Skills explicitly mentioned in the resume.
3. Work experience.
4. Education.
5. Resume score from 0 to 100.
6. Reasoning for the score.

Identify relevant technical and non-technical skills.
Do not invent information that is not present in the resume.

Return only valid JSON using this structure:

{{
    "candidate_name": "Name",
    "skills": ["Python", "SQL"],
    "experience": ["Experience details"],
    "education": ["Education details"],
    "score": 80,
    "reasoning": "Explanation of the score"
}}

Resume:
{resume_text}
"""

    elif prompt_version == "improved":

        prompt = f"""
You are a strict AI resume skill extraction system.

Analyze the resume and extract candidate information.

STRICT SKILL EXTRACTION RULES:

1. Focus primarily on Skills, Technical Skills,
   or Core Skills sections.
2. Extract only skills explicitly listed in these sections.
3. Do not extract technologies mentioned only in
   project descriptions or work experience.
4. Do not infer or assume skills.
5. Do not add related technologies.
6. Do not convert one skill into another.
7. Do not include duplicate skills.
8. Preserve the original skill names.
9. If a skill is not explicitly listed, do not include it.

Also extract:
1. Candidate name.
2. Work experience.
3. Education.
4. Resume score from 0 to 100.
5. Reasoning for the score.

Return only valid JSON using this exact structure:

{{
    "candidate_name": "Name",
    "skills": ["Python", "SQL"],
    "experience": ["Experience details"],
    "education": ["Education details"],
    "score": 80,
    "reasoning": "Explanation of the score"
}}

Resume:
{resume_text}
"""

    else:
        raise ValueError("Invalid prompt version")

    print(f"\nUsing Prompt Version: {prompt_version.upper()}")

    last_error = None
    total_tokens = 0

    for attempt in range(3):

        try:

            response_text = call_ollama(prompt)

            if isinstance(response_text, tuple):

                response_text, tokens = response_text

                total_tokens += tokens

            result = clean_json_response(response_text)

            result = validate_result(result)

            result["tokens_used"] = total_tokens

            return result

        except (
            json.JSONDecodeError,
            ValueError,
            TypeError
        ) as error:

            last_error = error

            print(
                f"Attempt {attempt + 1} failed: {error}"
            )

        except requests.RequestException as error:

            last_error = error

            print(
                f"Ollama connection error: {error}"
            )

    raise ValueError(
        f"Resume analysis failed after 3 attempts: {last_error}"
    )


@app.get("/health")
def health_check():

    try:

        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=10
        )

        response.raise_for_status()

        return {
            "status": "healthy",
            "ollama": "connected",
            "model": MODEL_NAME
        }

    except requests.RequestException:

        raise HTTPException(
            status_code=503,
            detail="Ollama is not available"
        )


@app.post("/analyze")
async def analyze_resume_api(
    file: UploadFile = File(...)
):

    filename = file.filename or ""

    extension = os.path.splitext(filename)[1].lower()

    if extension not in [".pdf", ".docx"]:

        raise HTTPException(
            status_code=415,
            detail="Only PDF and DOCX files are supported"
        )

    file_bytes = await file.read()

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    if len(file_bytes) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=413,
            detail="File size exceeds 10 MB"
        )

    try:

        resume_text = extract_text(
            file_bytes,
            filename
        )

        result = analyze_resume(
            resume_text,
            prompt_version="improved"
        )

        return {
            "filename": filename,
            "analysis": result
        }

    except ValueError as error:

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
