import base64
import json
import os
from io import BytesIO
import hashlib

from flask import Flask, make_response, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL', "postgresql://postgres:password@localhost/registration")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(basedir, "uploads")
app.config["CACHE_TYPE"] = "redis"
app.config["CACHE_REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))  # Ensure the API key is set in the environment
cache = Cache(app)

# Set up rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=os.getenv("REDIS_URL_RATE_LIMITS","redis://localhost:6379/1"), # Use Redis for storing rate limits
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
    default_limits=["200 per day", "50 per hour"]
)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(100), nullable=False)
    phoneNumber = db.Column(db.String(10), nullable=False)
    emailId = db.Column(db.String(120), nullable=False)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def generate_cache_key(image_path, prompt):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    image_hash = hashlib.sha256(image_data).hexdigest()
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    return f"{image_hash}_{prompt_hash}"

def extract_info(image_path, prompt):
    cache_key = generate_cache_key(image_path, prompt)
    cached_response = cache.get(cache_key)
    if cached_response:
        return cached_response
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt} Provide the output in JSON format.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encode_image(image_path)}",
                        },
                    },
                ],
            }
        ],
    )
    response_content = json.loads(response.choices[0].message.content)
    cache.set(cache_key, response_content, timeout=3600)  # Cache for 1 hour
    return response_content

def process_output(json_response):
    main_data = []
    subject_data = None

    for key, value in json_response.items():
        if isinstance(value, dict) and any(
            isinstance(v, (int, str)) for v in value.values()
        ):
            subject_data = [{"Subject": k, "Score": v} for k, v in value.items()]
        else:
            main_data.append({"Field": key, "Value": value})

    return main_data, subject_data

def generate_pdf(output_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch
    )
    elements = []
    styles = getSampleStyleSheet()

    styles["Title"].fontSize = 16
    styles["Title"].alignment = 1  # Center alignment

    styles.add(
        ParagraphStyle(
            name="Subtitle", parent=styles["Heading2"], fontSize=14, alignment=1
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader", parent=styles["Normal"], fontSize=10, alignment=1
        )
    )

    elements.append(Paragraph("Universal College Application", styles["Title"]))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph("First-Year Admissions Application", styles["Subtitle"]))
    elements.append(Spacer(1, 0.25 * inch))

    for i, data in enumerate(output_data):
        if data:
            title = [
                "Personal Information",
                "10th Grade Results",
                "12th Grade Results",
            ][i]
            elements.append(Paragraph(title, styles["Heading2"]))
            elements.append(Spacer(1, 0.1 * inch))

            if "error" in data:
                elements.append(Paragraph(f"Error: {data['error']}", styles["Normal"]))
            else:
                main_data = [
                    [
                        Paragraph(str(item["Field"]), styles["TableHeader"]),
                        Paragraph(str(item["Value"]), styles["Normal"]),
                    ]
                    for item in data["main"]
                ]
                main_table = Table(main_data, colWidths=[2.5 * inch, 4 * inch])
                main_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ]
                    )
                )
                elements.append(main_table)
                elements.append(Spacer(1, 0.1 * inch))

                if data["subjects"]:
                    elements.append(Paragraph("Subject Scores", styles["Heading3"]))
                    elements.append(Spacer(1, 0.1 * inch))
                    subject_data = [
                        [
                            Paragraph("Subject", styles["TableHeader"]),
                            Paragraph("Score", styles["TableHeader"]),
                        ]
                    ] + [
                        [
                            Paragraph(str(item["Subject"]), styles["Normal"]),
                            Paragraph(str(item["Score"]), styles["Normal"]),
                        ]
                        for item in data["subjects"]
                    ]
                    subject_table = Table(subject_data, colWidths=[3 * inch, 3 * inch])
                    subject_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, 0), 10),
                                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                                ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                                ("FONTSIZE", (0, 1), (-1, -1), 10),
                                ("TOPPADDING", (0, 1), (-1, -1), 6),
                                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ]
                        )
                    )
                    elements.append(subject_table)

            elements.append(Spacer(1, 0.25 * inch))

    doc.build(elements)
    buffer.seek(0)
    return buffer

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/digiform", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def digiform():
    if request.method == "POST":
        fullName = request.form["fullName"]
        phoneNumber = request.form["phoneNumber"]
        emailId = request.form["emailId"]

        registration = Registration(
            fullName=fullName,
            phoneNumber=phoneNumber,
            emailId=emailId,
        )
        db.session.add(registration)
        db.session.commit()
        return redirect(url_for("upload_form"))
    return render_template("register.html")

@app.route("/upload", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def upload_form():
    if request.method == "POST":
        output_data = []
        prompts = [
            'Extract the following information from the Aadhar card image: Full Name, Fathers Name, Date of Birth, Address, Aadhar Number, Gender. If any field is not clearly visible or cannot be extracted, return "Not Available" for that field. If the image is not a valid Aadhar card, return "Invalid Image: Not an Aadhar card".',
            'Extract the following information from the 10th standard marksheet image: Seat Number, Year of Passing, Subject Names with scores, Total Marks Obtained, Percentage. Return each subject score separately. If any field is not clearly visible or cannot be extracted, return "Not Available" for that field. If the image is not a valid 10th standard marksheet, return "Invalid Image: Not a 10th standard marksheet".',
            'Extract the following information from the 12th standard marksheet image: Stream, Seat Number, Year of Passing, Subject Names with scores, Total Marks Obtained, Percentage. Return each subject score separately. If any field is not clearly visible or cannot be extracted, return "Not Available" for that field. If the image is not a valid 12th standard marksheet, return "Invalid Image: Not a 12th standard marksheet".',
        ]

        for i, field in enumerate(
            ["identityDocument", "tenthMarksheet", "twelfthMarksheet"]
        ):
            file = request.files.get(field)
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                try:
                    json_response = extract_info(filepath, prompts[i])
                    print(json_response)
                    main_data, subject_data = process_output(json_response)
                    output_data.append({"main": main_data, "subjects": subject_data})
                except Exception as e:
                    output_data.append({"error": str(e)})
                finally:
                    if os.path.exists(filepath):
                        os.remove(filepath)  # Remove the file after processing
            else:
                output_data.append(None)

        pdf_buffer = generate_pdf(output_data)
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")
        return render_template("form.html", pdf_data=pdf_base64)
    return render_template("form.html")

@app.route("/download_pdf", methods=["POST"])
@limiter.limit("10 per minute")
def download_pdf():
    pdf_base64 = request.form.get("pdf_data")
    if pdf_base64:
        pdf_data = base64.b64decode(pdf_base64)
        response = make_response(pdf_data)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            "attachment; filename=digiform_results.pdf"
        )
        return response
    return "PDF not found", 404

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    print(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=5001, debug=False)
