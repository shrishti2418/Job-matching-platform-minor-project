import re
from django.shortcuts import render, redirect
from .form import ResumeForm
from .utils import extract_resume_data, calculate_experience, extract_text_from_docx, extract_text_from_pdf

def upload_resume(request):
    if request.method == "POST":
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume_instance = form.save(commit=False)
            resume_file = request.FILES["file"]
            file_name = resume_file.name.lower()

            if file_name.endswith('.pdf'):
                file_type = "pdf"
            elif file_name.endswith('.docx'):
                file_type = "docx"
            else:
                # Unsupported file type
                form.add_error('file', 'Unsupported file type. Please upload a PDF or DOCX file.')
                return render(request, "extractor/upload.html", {"form": form})

            # Extract resume data using utility function
            data = extract_resume_data(resume_file, file_type=file_type)

            # Check if extraction returned error or empty text
            if "error" in data or not data.get("summary"):
                form.add_error('file', 'Failed to extract data from the resume. Please upload a valid PDF or DOCX file.')
                return render(request, "extractor/upload.html", {"form": form})

            # Assign extracted data to resume instance
            resume_instance.skills = ", ".join(data.get("skills", []))
            resume_instance.summary = data.get("summary", "")
            resume_instance.experience = data.get("experience", "Fresher")
            resume_instance.education = data.get("education", "")
            resume_instance.projects = data.get("projects", "")
            achievements = data.get("achievements")
            if isinstance(achievements, list):
                resume_instance.achievements = ", ".join(achievements)
            else:
                resume_instance.achievements = achievements or ""

            # Add GitHub links and career objective manually or from extracted data if available
            github_links = data.get("github_links", "")
            if not github_links:
                # Try to extract GitHub links from the text if not directly extracted
                text = ""
                if file_type == "docx":
                    text = extract_text_from_docx(resume_file)
                elif file_type == "pdf":
                    text = extract_text_from_pdf(resume_file)
                github_links = ", ".join(re.findall(r"https?://github\.com/[^\s]+", text))
            resume_instance.github_links = github_links

            # Update career objective manually as per user request
            career_objective = "Actively seeking Python/Backend Developer roles where I can apply my skills in API development, databases, and backend systems."
            resume_instance.summary = career_objective

            resume_instance.save()

            return render(request, "extractor/upload.html", {
                "form": ResumeForm(),
                "skills": resume_instance.skills,
                "summary": resume_instance.summary,
                "experience": resume_instance.experience,
                "achievements": resume_instance.achievements,
                "total_experience": calculate_experience(resume_instance.summary + " " + resume_instance.experience),
                "projects": resume_instance.projects,
                "education": resume_instance.education,
                "github_links": resume_instance.github_links,
                "message": "Resume uploaded and processed successfully."
            })
        else:
            return render(request, "extractor/upload.html", {"form": form})

    else:
        form = ResumeForm()
        return render(request, "extractor/upload.html", {"form": form})


def ats_checker_view(request):
    if request.method == "POST":
        job_description = request.POST.get("job_description", "").strip()
        resume_file = request.FILES.get("resume_file")

        if not job_description:
            return render(request, "extractor/ats_checker.html", {
                "error": "Please provide a job description."
            })

        if not resume_file:
            return render(request, "extractor/ats_checker.html", {
                "error": "Please upload a resume file."
            })

        # Determine file type
        file_name = resume_file.name.lower()
        if file_name.endswith('.pdf'):
            file_type = "pdf"
            resume_text = extract_text_from_pdf(resume_file)
        elif file_name.endswith('.docx'):
            file_type = "docx"
            resume_text = extract_text_from_docx(resume_file)
        else:
            return render(request, "extractor/ats_checker.html", {
                "error": "Unsupported file type. Please upload a PDF or DOCX file."
            })

        if not resume_text:
            return render(request, "extractor/ats_checker.html", {
                "error": "Failed to extract text from the resume."
            })

        # Import ats_checker from utils
        from .utils import ats_checker

        # Perform ATS check
        ats_result = ats_checker(resume_text, job_description)

        if "error" in ats_result:
            return render(request, "extractor/ats_checker.html", {
                "error": ats_result["error"]
            })

        missing_count = ats_result["total_jd_keywords"] - ats_result["match_count"]
        missing_indices = list(range(missing_count))
        return render(request, "extractor/ats_checker.html", {
            "job_description": job_description,
            "ats_result": ats_result,
            "missing_count": missing_count,
            "missing_indices": missing_indices,
            "resume_text": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text  # Preview
        })

    else:
        return render(request, "extractor/ats_checker.html")
    

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import extract_text_from_pdf, extract_text_from_docx, ats_checker

@api_view(["POST"])
def ats_checker_api(request):
    job_description = request.data.get("job_description", "").strip()
    resume_file = request.FILES.get("resume_file")

    if not job_description:
        return Response({"error": "Please provide a job description."}, status=400)
    if not resume_file:
        return Response({"error": "Please upload a resume file."}, status=400)

    file_name = resume_file.name.lower()
    if file_name.endswith('.pdf'):
        resume_text = extract_text_from_pdf(resume_file)
    elif file_name.endswith('.docx'):
        resume_text = extract_text_from_docx(resume_file)
    else:
        return Response({"error": "Unsupported file type."}, status=400)

    if not resume_text:
        return Response({"error": "Failed to extract text from the resume."}, status=500)

    ats_result = ats_checker(resume_text, job_description)

    if "error" in ats_result:
        return Response({"error": ats_result["error"]}, status=500)

    return Response({
        "job_description": job_description,
        "ats_result": ats_result,
        "resume_preview": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text
    })





    

    
