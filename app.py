import base64
import json
import os
from io import BytesIO

from flask import Flask, make_response, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.utils import secure_filename

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "registration.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(basedir, "uploads")

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)
client = OpenAI()


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(100), nullable=False)
    phoneNumber = db.Column(db.String(10), nullable=False)
    emailId = db.Column(db.String(120), nullable=False)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def extract_info(image_path, prompt):
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
    return json.loads(response.choices[0].message.content)


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

    # Update existing styles
    styles["Title"].fontSize = 16
    styles["Title"].alignment = 1  # Center alignment

    # Add new styles
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

    # Title
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
                # Main data table
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

                # Subject data table (if available)
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
    app.run(debug=True)
