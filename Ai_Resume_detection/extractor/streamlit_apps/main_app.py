import os
import sys
import django
from pathlib import Path
import tempfile
import json
import io

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ai_Resume_detection.settings')
django.setup()

# Import your existing Django utilities and models
from extractor.utils import (
    extract_resume_data, 
    ats_checker,
    extract_text_from_pdf,
    extract_text_from_docx,
    ask_google_generativeai
)
from extractor.models import Resume
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json

# Page configuration
st.set_page_config(
    page_title="AI Resume Detection & ATS Checker",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .skills-tag {
        background-color: #e1f5fe;
        color: #01579b;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        border-radius: 0.25rem;
        display: inline-block;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# def save_resume_to_database-------> removed(uploaded_file, extracted_data, name="", email=""):
#     """Save resume and extracted data to Django database using your existing model"""
#     try:
#         # Create file content
#         file_content = ContentFile(uploaded_file.read(), name=uploaded_file.name)
        
#         # Create Resume instance using your existing model
#         resume_instance = Resume.objects.create(
#             name=name or f"User_{uploaded_file.name}",
#             email=email or "",
#             file=file_content,
#             skills=", ".join(extracted_data.get('skills', [])) if extracted_data.get('skills') else "",
#             summary=extracted_data.get('summary', ''),
#             experience=extracted_data.get('experience', ''),
#             education=extracted_data.get('education', ''),
#             projects=extracted_data.get('projects', ''),
#             achievements=json.dumps(extracted_data.get('achievements', [])) if extracted_data.get('achievements') else "",
#             github_links=extracted_data.get('github_links', '')
#         )
        
#         return resume_instance
    
#     except Exception as e:
#         st.error(f"Error saving to database: {e}")
#         return None

# <-----------extraction start------------------->

def extract_text_from_uploaded_file(uploaded_file):
    """Extract text from uploaded file using your existing utils functions"""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'pdf':
            return extract_text_from_pdf(uploaded_file)
        elif file_extension in ['docx', 'doc']:
            return extract_text_from_docx(uploaded_file)
        else:
            st.error("Unsupported file format")
            return ""
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return ""
    
# <--------extraction end------------------->

# <-----------Display Functions start: without ats-------------------> 

def display_resume_analysis(extracted_data):
    """Display comprehensive resume analysis results"""
    
    st.subheader("📊 Resume Analysis Results")
    
    # Basic Information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Summary")
        summary = extracted_data.get('summary', 'No summary found')
        st.info(summary)
        
        st.markdown("### 💼 Experience")
        experience = extracted_data.get('experience', 'No experience found')
        total_exp = extracted_data.get('total_experience', 'Not calculated')
        st.write(f"**Total Experience:** {total_exp}")
        st.write(experience)
    
    with col2:
        st.markdown("### 🎓 Education")
        education = extracted_data.get('education', 'No education information found')
        st.write(education)
        
        st.markdown("### 🚀 Projects")
        projects = extracted_data.get('projects', 'No projects found')
        st.write(projects)
    
    # Skills Section
    skills = extracted_data.get('skills', [])
    if skills:
        st.markdown("### 🛠️ Skills")
        
        # Display skills as tags
        skills_html = ""
        for skill in skills:
            skills_html += f'<span class="skills-tag">{skill}</span>'
        st.markdown(skills_html, unsafe_allow_html=True)
        
        # Skills chart
        # if len(skills) > 1:
        #     fig = px.bar(
        #         x=skills[:10],  # Top 10 skills
        #         y=[1] * len(skills[:10]),
        #         title="Top Skills Found in Resume",
        #         labels={'x': 'Skills', 'y': 'Count'}
        #     )
        #     fig.update_layout(showlegend=False)
        #     st.plotly_chart(fig, use_container_width=True)
    
    # Achievements
    achievements = extracted_data.get('achievements', [])
    if achievements:
        st.markdown("### 🏆 Achievements")
        for i, achievement in enumerate(achievements, 1):
            st.write(f"{i}. {achievement}")
    
    # GitHub Links
    github_links = extracted_data.get('github_links', '')
    if github_links:
        st.markdown("### 🔗 GitHub Links")
        st.write(github_links)

# <-----------Display Functions end: without ats-------------------> 

# <-----------Display Functions start: WITH ats-------------------> 

def display_ats_results(ats_result, resume_text):
    """Display ATS analysis results with visualizations"""
    
    if 'error' in ats_result:
        st.error(f"ATS Analysis Error: {ats_result['error']}")
        return
    
    st.success("✅ ATS Analysis Complete!")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_keywords = ats_result.get('total_jd_keywords', 0)
    matched_count = ats_result.get('match_count', 0)
    match_percentage = ats_result.get('match_percentage', 0)
    
    with col1:
        st.metric("Total JD Keywords", total_keywords)
    
    with col2:
        st.metric("Matched Keywords", matched_count)
    
    with col3:
        st.metric("Match Percentage", f"{match_percentage}%")
    
    with col4:
        # ATS Score interpretation
        if match_percentage >= 80:
            st.metric("ATS Score", "Excellent 🎉", delta="High compatibility")
        elif match_percentage >= 60:
            st.metric("ATS Score", "Good 👍", delta="Good compatibility")
        elif match_percentage >= 40:
            st.metric("ATS Score", "Fair ⚠️", delta="Needs improvement")
        else:
            st.metric("ATS Score", "Poor 😞", delta="Major improvements needed")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        fig_pie = px.pie(
            values=[matched_count, total_keywords - matched_count],
            names=['Matched', 'Missing'],
            title="Keyword Match Distribution",
            color_discrete_map={'Matched': '#00cc44', 'Missing': '#ff4444'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Progress indicator
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = match_percentage,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "ATS Compatibility Score"},
            delta = {'reference': 70},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Keyword analysis
    matched_keywords = ats_result.get('matched_keywords', [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if matched_keywords:
            st.subheader("✅ Matched Keywords")
            # Display first 20 matched keywords
            for keyword in matched_keywords[:20]:
                st.markdown(f'<span style="background-color: #d4edda; color: #155724; padding: 0.25rem 0.5rem; margin: 0.25rem; border-radius: 0.25rem; display: inline-block;">{keyword}</span>', unsafe_allow_html=True)
            
            if len(matched_keywords) > 20:
                st.info(f"... and {len(matched_keywords) - 20} more matched keywords")
    
    with col2:
        # Missing keywords (calculate from total vs matched)
        all_jd_keywords = set(ats_result.get('matched_keywords', []))
        # Note: Your ats_checker function doesn't return missing keywords directly
        # but we can show improvement suggestions
        st.subheader("💡 Improvement Suggestions")
        
        if match_percentage < 60:
            st.warning("""
            **Recommendations:**
            - Add more relevant technical keywords from the job description
            - Include industry-specific terminology
            - Mention relevant tools and technologies
            - Add action verbs that match the job requirements
            """)
        elif match_percentage < 80:
            st.info("""
            **Good Match! Consider:**
            - Fine-tuning with a few more specific keywords
            - Adding relevant certifications mentioned in the JD
            - Including measurable achievements
            """)
        else:
            st.success("""
            **Excellent Match!**
            - Your resume is well-optimized for this position
            - Great keyword alignment with the job description
            - Keep up the excellent work!
            """)
    
    # # Resume text preview
    # with st.expander("📄 Extracted Resume Text"):
    #     st.text_area("Resume Content", value=resume_text, height=300, disabled=True)

# <-----------Display Functions end: WITH ats-------------------> 

def main():
    st.markdown('<h1 class="main-header">📄 AI Resume Detection & ATS Checker</h1>', unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📁 Upload & Analyze", "🎯 ATS Checker", "ℹ️ About"])
    
    with tab1:
        st.header("📁 Upload Resume & Extract Information")
        st.markdown("Upload your resume to extract detailed information using AI-powered analysis.")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf'],
            help="Upload your resume in PDF format"
        )
        
        if uploaded_file:
            # Optional: User information
            with st.expander("📝 Optional: Add Your Information"):
                col1, col2 = st.columns(2)
                with col1:
                    user_name = st.text_input("Your Name", placeholder="Enter your name")
                with col2:
                    user_email = st.text_input("Your Email", placeholder="Enter your email")
            
            if st.button("🔍 Analyze Resume", type="primary"):
                with st.spinner("Analyzing your resume... This may take a moment."):
                    # Determine file type
                    file_extension = uploaded_file.name.split('.')[-1].lower()
                    file_type = 'docx' if file_extension in ['docx', 'doc'] else 'pdf'
                    
                    # Extract resume data using your existing function
                    extracted_data = extract_resume_data(uploaded_file, file_type)
                    
                    if 'error' in extracted_data:
                        st.error(f"Error processing resume: {extracted_data['error']}")
                    else:
                        # Display analysis results
                        display_resume_analysis(extracted_data)
                        
                        # Save to database------>>>>Changed.....commented
                        # if st.button("💾 Save Analysis to Database"):
                        #     resume_instance = save_resume_to_database(
                        #         uploaded_file, 
                        #         extracted_data, 
                        #         user_name, 
                        #         user_email
                        #     )
                        #     if resume_instance:
                        #         st.success(f"✅ Resume analysis saved! ID: {resume_instance.id}")
    
    with tab2:
        st.header("🎯 ATS Resume Checker")
        st.markdown("Compare your resume against a job description to check ATS compatibility.")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📄 Upload Resume")
            ats_resume_file = st.file_uploader(
                "Choose your resume file",
                type=['pdf'],
                key="ats_resume"
            )
        
        with col2:
            st.subheader("💼 Job Description")
            job_description = st.text_area(
                "Paste the complete job description here",
                height=200,
                placeholder="Copy and paste the job description from the job posting...",
                help="Include the complete job description for accurate analysis"
            )
        
        if st.button("🔍 Check ATS Compatibility", type="primary") and ats_resume_file and job_description:
            if len(job_description.strip()) < 50:
                st.warning("⚠️ Job description seems too short. Please provide a more detailed description.")
            else:
                with st.spinner("🔄 Analyzing ATS compatibility... This may take a moment."):
                    # Extract text from resume
                    resume_text = extract_text_from_uploaded_file(ats_resume_file)
                    
                    if resume_text:
                        # Perform ATS analysis using your existing function
                        ats_result = ats_checker(resume_text, job_description)
                        
                        # Display results
                        display_ats_results(ats_result, resume_text)
                    else:
                        st.error("❌ Could not extract text from the uploaded resume file.")
    
    # changes made here...commented
    # with tab3:
    #     st.header("📊 Saved Resume Database")
    #     st.markdown("View previously analyzed resumes from your database.")
        
    #     # Load resumes from database
    #     try:
    #         recent_resumes = Resume.objects.all().order_by('-uploaded_at')[:10]
            
    #         if recent_resumes.exists():
    #             for resume in recent_resumes:
    #                 with st.expander(f"📄 {resume.name} - {resume.uploaded_at.strftime('%Y-%m-%d %H:%M')}"):
    #                     col1, col2, col3 = st.columns(3)
                        
    #                     with col1:
    #                         st.write(f"**Name:** {resume.name}")
    #                         st.write(f"**Email:** {resume.email}")
    #                         st.write(f"**File:** {resume.file.name}")
                        
    #                     with col2:
    #                         st.write(f"**Skills:** {resume.skills[:100]}..." if len(resume.skills) > 100 else resume.skills)
    #                         st.write(f"**Experience:** {resume.experience[:100]}..." if len(resume.experience) > 100 else resume.experience)
                        
    #                     with col3:
    #                         if resume.github_links:
    #                             st.write(f"**GitHub:** {resume.github_links}")
                            
    #                         # Download button for resume file
    #                         if st.button(f"📥 Download Resume", key=f"download_{resume.id}"):
    #                             st.info("Download functionality can be implemented here")
                        
    #                     # Show full summary
    #                     if resume.summary:
    #                         st.markdown("**Summary:**")
    #                         st.write(resume.summary)
    #         else:
    #             st.info("No resumes found in database. Upload and analyze some resumes first!")
                
    #     except Exception as e:
    #         st.error(f"Error loading resumes from database: {e}")
    
    with tab3:
        st.header("ℹ️ About This Application")
        
        st.markdown("""
        ### 🚀 Features
        
        **Resume Analysis:**
        - Extract comprehensive information from PDF, DOC, DOCX, and TXT files
        - Identify skills, experience, education, projects, and achievements
        - Calculate total work experience automatically
        - Extract GitHub links and contact information
        
        **ATS Compatibility Checker:**
        - Compare resume against job descriptions
        - Calculate keyword match percentage
        - Provide improvement recommendations
        - Visual analytics and insights
        
        **Database Integration:**
        - Save analyzed resumes to Django database
        - View analysis history
        - Track improvements over time
        
        ### 🛠️ Technology Stack
        - **Backend:** Django with SpaCy NLP
        - **Frontend:** Streamlit
        - **Analysis:** Custom regex and NLP algorithms
        - **Database:** Django ORM with SQLite/PostgreSQL
        
        ### 📊 How ATS Analysis Works
        1. **Text Extraction:** Extract clean text from resume files
        2. **Keyword Matching:** Compare resume keywords with job description
        3. **Scoring:** Calculate compatibility percentage
        4. **Recommendations:** Provide specific improvement suggestions
        
        ### 💡 Tips for Better ATS Scores
        - Use keywords from the job description naturally in your resume
        - Include relevant technical skills and tools
        - Add measurable achievements and results
        - Use standard section headings (Experience, Education, Skills)
        
        """)
        
        # System information
        st.subheader("🔧 System Information")
        col1, col2 = st.columns(2)
        
        with col1:
            total_resumes = Resume.objects.count()
            st.metric("Total Resumes Processed", total_resumes)
        
        with col2:
            st.metric("Supported Formats", "PDF")
        
        

if __name__ == "__main__":
    main()
