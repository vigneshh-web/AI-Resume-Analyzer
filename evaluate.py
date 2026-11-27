
from Task3 import extract_text, analyze_resume
import os
import re

RESUME_FOLDER = "Resumes"

golden_dataset = {
    "Resume_1.pdf": [
        "Python", "Java", "SQL", "Data Structures",
        "Arduino", "HTML", "CSS", "Git"
    ],
    "Resume_2.pdf": [
        "Market Research", "Advanced Excel", "Power BI",
        "Sales Forecasting", "Financial Statement Analysis",
        "Google Analytics", "PowerPoint", "SPSS"
    ],
    "Resume_3.txt": [
        "Content Writing", "Copy Editing",
        "English-Hindi Translation", "SEO", "WordPress",
        "MS Word", "Excel", "Google Docs", "Desk Research"
    ],
    "Resume_4.pdf": [
        "PHP", "Laravel", "JavaScript", "MySQL",
        "HTML5", "CSS3", "Bootstrap", "Python",
        "Git", "GitHub"
    ],
    "Resume_5.txt": [
        "TallyPrime", "GST Returns", "Bank Reconciliation",
        "Advanced Excel", "Journal Entries", "TDS",
        "Accounts Payable", "MS Word"
    ],
    "Resume_6.pdf": [
        "Python", "Java", "SQL", "MySQL", "HTML",
        "CSS", "JavaScript", "Git", "Visual Studio Code"
    ],
    "Resume_7.pdf": [
        "SQL", "Excel", "Power BI", "Tableau",
        "Python", "Pandas", "Data Cleaning", "A/B Testing"
    ],
    "Resume_8.pdf": [
        "Angular", "TypeScript", "JavaScript", "HTML5",
        "CSS3", "SCSS", "RxJS", "Tailwind CSS", "Figma"
    ]
}


def normalize_skill(skill):
    return re.sub(r"\s+", " ", skill.strip().lower())


def calculate_metrics(expected_skills, extracted_skills):

    expected = {
        normalize_skill(skill)
        for skill in expected_skills
    }

    extracted = {
        normalize_skill(skill)
        for skill in extracted_skills
        if isinstance(skill, str) and skill.strip()
    }

    tp = len(expected & extracted)
    fp = len(extracted - expected)
    fn = len(expected - extracted)

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0

    union = expected | extracted
    accuracy = tp / len(union) if union else 0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy
    }


def evaluate_prompt(prompt_version):

    total_tp = 0
    total_fp = 0
    total_fn = 0

    accuracy_scores = []
    resume_scores = {}

    print(f"\n========== {prompt_version.upper()} PROMPT EVALUATION ==========")

    for filename, expected_skills in golden_dataset.items():

        file_path = os.path.join(RESUME_FOLDER, filename)

        print(f"\nProcessing: {filename}")

        if not os.path.exists(file_path):
            print("FAILED: File not found.")
            continue

        try:
            with open(file_path, "rb") as file:
                file_bytes = file.read()

            if filename.lower().endswith(".txt"):
                resume_text = file_bytes.decode("utf-8")
            else:
                resume_text = extract_text(file_bytes, filename)

            if not resume_text.strip():
                print("SKIPPED: Empty resume.")
                continue

            result = analyze_resume(
                resume_text,
                prompt_version=prompt_version
            )

            if not isinstance(result, dict):
                print("FAILED: Invalid analysis result.")
                continue

            extracted_skills = result.get("skills", [])

            if not isinstance(extracted_skills, list):
                print("FAILED: Skills output is invalid.")
                continue

            metrics = calculate_metrics(
                expected_skills,
                extracted_skills
            )

            total_tp += metrics["tp"]
            total_fp += metrics["fp"]
            total_fn += metrics["fn"]

            accuracy_scores.append(metrics["accuracy"])

            score = result.get("score")

            if isinstance(score, (int, float)):
                resume_scores[filename] = score

            print(f"Precision: {metrics['precision']:.2f}")
            print(f"Recall: {metrics['recall']:.2f}")
            print(f"Extraction Accuracy: {metrics['accuracy']:.2f}")
            print(f"Resume Score: {score}")

        except ValueError as error:
            if "No text found" in str(error):
                print("SKIPPED: Scanned PDF - OCR not supported.")
            else:
                print(f"FAILED: {error}")

        except Exception as error:
            print(f"FAILED: {error}")

    precision = (
        total_tp / (total_tp + total_fp)
        if (total_tp + total_fp) else 0
    )

    recall = (
        total_tp / (total_tp + total_fn)
        if (total_tp + total_fn) else 0
    )

    accuracy = (
        sum(accuracy_scores) / len(accuracy_scores)
        if accuracy_scores else 0
    )

    average_score = (
        sum(resume_scores.values()) / len(resume_scores)
        if resume_scores else 0
    )

    return {
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "average_score": average_score,
        "resume_scores": resume_scores,
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "processed": len(accuracy_scores)
    }


original = evaluate_prompt("original")
improved = evaluate_prompt("improved")


print("\n")
print("=" * 65)
print("                 PROMPT IMPROVEMENT COMPARISON")
print("=" * 65)

print(f"{'Metric':<30}{'Original':<17}{'Improved':<17}")
print("-" * 65)

print(
    f"{'Precision':<30}"
    f"{original['precision']:<17.2f}"
    f"{improved['precision']:<17.2f}"
)

print(
    f"{'Recall':<30}"
    f"{original['recall']:<17.2f}"
    f"{improved['recall']:<17.2f}"
)

print(
    f"{'Extraction Accuracy':<30}"
    f"{original['accuracy']:<17.2f}"
    f"{improved['accuracy']:<17.2f}"
)

print(
    f"{'Average Resume Score':<30}"
    f"{original['average_score']:<17.2f}"
    f"{improved['average_score']:<17.2f}"
)

print("-" * 65)

print(
    f"{'Precision Improvement':<30}"
    f"{improved['precision'] - original['precision']:+.2f}"
)

print(
    f"{'Recall Improvement':<30}"
    f"{improved['recall'] - original['recall']:+.2f}"
)

print(
    f"{'Accuracy Improvement':<30}"
    f"{improved['accuracy'] - original['accuracy']:+.2f}"
)

common_resumes = (
    set(original["resume_scores"])
    & set(improved["resume_scores"])
)

if common_resumes:
    score_differences = [
        abs(
            original["resume_scores"][name]
            - improved["resume_scores"][name]
        )
        for name in common_resumes
    ]

    average_score_difference = (
        sum(score_differences) / len(score_differences)
    )

    print(
        f"{'Average Score Difference':<30}"
        f"{average_score_difference:.2f}"
    )

else:
    print("Average Score Difference: N/A")


print("-" * 65)
print(f"Original processed resumes: {original['processed']}")
print(f"Improved processed resumes: {improved['processed']}")

print("=" * 65)
print("EVALUATION COMPLETED")
print("Original Prompt: Version 1")
print("Improved Prompt: Version 2")
print("=" * 65)
