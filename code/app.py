import flask
from flask import flash, request
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = flask.Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))
app.config["SECRET_KEY"] = "dev"

# Backend API base URL
BACKEND_URL = "http://localhost:5001"


@app.route("/")
def home():
    return flask.render_template("home.html")


@app.route("/patients", methods=["GET", "POST"])
def patients():
    error_message = None

    if request.method == "POST":
        # Collect form data
        name = request.form.get("name", "").strip()
        diagnosis = request.form.get("diagnosis", "").strip()
        treatment = request.form.get("treatment", "").strip()
        priority = request.form.get("priority", "").strip()

        # Frontend validation (before sending to backend)
        errors = []
        if not name or len(name) > 20:
            errors.append("Name is required and must be 20 characters or fewer.")
        if not diagnosis or len(diagnosis) > 20:
            errors.append("Diagnosis is required and must be 20 characters or fewer.")
        if not treatment or len(treatment) > 20:
            errors.append("Treatment is required and must be 20 characters or fewer.")
        try:
            priority_int = int(priority)
            if priority_int < 1 or priority_int > 10:
                errors.append("Priority must be between 1 and 10.")
        except (ValueError, TypeError):
            errors.append("Priority must be a valid integer.")

        if errors:
            flash(" ".join(errors), "danger")
            return flask.redirect(flask.url_for("patients"))
        else:
            # Send POST request to backend API
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/patients",
                    json={
                        "name": name,
                        "diagnosis": diagnosis,
                        "treatment": treatment,
                        "priority": priority_int
                    }
                )
                if response.status_code == 201:
                    flash("Patient added successfully!", "success")
                    return flask.redirect(flask.url_for("patients"))
                else:
                    # Backend returned an error (extra security layer caught something)
                    try:
                        resp_data = response.json()
                        flash(" ".join(resp_data.get("errors", ["Unknown error from backend."])), "danger")
                    except ValueError:
                        flash("Backend returned an invalid response.", "danger")
                    return flask.redirect(flask.url_for("patients"))
            except requests.exceptions.ConnectionError:
                flash("Could not connect to the backend server. Is it running on port 5001?", "danger")
                return flask.redirect(flask.url_for("patients"))

    # Fetch all patients from backend via GET
    patient_info = []
    try:
        response = requests.get(f"{BACKEND_URL}/api/patients")
        if response.status_code == 200:
            patient_info = response.json().get("patients", [])
        else:
            error_message = "Could not load patients from the backend."
    except requests.exceptions.ConnectionError:
        error_message = "Could not connect to the backend server. Is it running on port 5001?"

    return flask.render_template(
        "patients_table.html",
        patient_info=patient_info,
        error_message=error_message
    )


@app.route("/delete/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    try:
        response = requests.delete(f"{BACKEND_URL}/api/patients/{patient_id}")
        if response.status_code == 200:
            flash("Patient deleted successfully!", "success")
        else:
            try:
                resp_data = response.json()
                flash(" ".join(resp_data.get("errors", ["Unknown error from backend."])), "danger")
            except ValueError:
                flash("Backend returned an invalid response.", "danger")
    except requests.exceptions.ConnectionError:
        flash("Could not connect to the backend server. Is it running on port 5001?", "danger")

    return flask.redirect(flask.url_for("patients"))


if __name__ == "__main__":
    app.run(port=5000, debug=True)
