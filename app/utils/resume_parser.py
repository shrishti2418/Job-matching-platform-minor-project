import pdfplumber

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

parsed_text = extract_text_from_pdf("D:\\Minor-Project\\data\\resume1.pdf")
print(parsed_text)