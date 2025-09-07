 
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Static & Templates config
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Home page (resume upload)
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Upload resume (dummy handling)
@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    # ⚡ For now, we are not parsing the resume
    # Later: save file, extract skills via NLP
    return RedirectResponse(url="/results", status_code=303)

# Results page (dummy data)
@app.get("/results", response_class=HTMLResponse)
async def results(request: Request):
    dummy_data = {
        "skills": ["Python", "SQL", "Machine Learning"],
        "jobs": [
            {"title": "Data Analyst", "score": "75%", "missing": "PowerBI", "course": "https://www.coursera.org"},
            {"title": "ML Engineer", "score": "60%", "missing": "TensorFlow", "course": "https://www.youtube.com"},
        ]
    }
    return templates.TemplateResponse("results.html", {"request": request, "data": dummy_data})
