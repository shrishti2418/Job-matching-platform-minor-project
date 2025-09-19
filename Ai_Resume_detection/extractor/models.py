from django.db import models

class Resume(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    file = models.FileField(upload_to='resumes/')
    skills = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    github_links = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
