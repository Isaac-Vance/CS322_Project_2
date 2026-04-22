import flask
from flask import request, jsonify
import sqlite3
from pathlib import Path

app = flask.Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "patients.db"


def get_db():
    """Get a database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the patients table if it doesn't already exist."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            diagnosis TEXT NOT NULL,
            treatment TEXT NOT NULL,
            priority INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def validate_patient_data(data):
    """
    Validate patient data received from a POST request.
    Returns (is_valid, errors) tuple.
    This is the BACKEND security layer -- even if someone bypasses
    the frontend (e.g. using Postman), these checks still run.
    """
    errors = []

    # Check that all required fields are present
    for field in ["name", "diagnosis", "treatment", "priority"]:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate name: non-empty string, max 20 characters
    name = data.get("name", "")
    if not isinstance(name, str) or len(name.strip()) == 0:
        errors.append("Name must be a non-empty string.")
    elif len(name) > 20:
        errors.append("Name must be 20 characters or fewer.")

    # Validate diagnosis: non-empty string, max 20 characters
    diagnosis = data.get("diagnosis", "")
    if not isinstance(diagnosis, str) or len(diagnosis.strip()) == 0:
        errors.append("Diagnosis must be a non-empty string.")
    elif len(diagnosis) > 20:
        errors.append("Diagnosis must be 20 characters or fewer.")

    # Validate treatment: non-empty string, max 20 characters
    treatment = data.get("treatment", "")
    if not isinstance(treatment, str) or len(treatment.strip()) == 0:
        errors.append("Treatment must be a non-empty string.")
    elif len(treatment) > 20:
        errors.append("Treatment must be 20 characters or fewer.")

    # Validate priority: must be a positive integer between 1 and 10
    priority = data.get("priority")
    try:
        priority_int = int(priority)
        if priority_int < 1 or priority_int > 10:
            errors.append("Priority must be between 1 and 10.")
    except (ValueError, TypeError):
        errors.append("Priority must be a valid integer.")

    return len(errors) == 0, errors


# ──────────────────────────────────────────────
#  API Endpoints
# ──────────────────────────────────────────────

@app.route("/api/patients", methods=["GET"])
def get_patients():
    """Return all patients from the database as JSON."""
    conn = get_db()
    rows = conn.execute("SELECT id, name, diagnosis, treatment, priority FROM patients").fetchall()
    conn.close()

    patients = [
        {
            "id": row["id"],
            "name": row["name"],
            "diagnosis": row["diagnosis"],
            "treatment": row["treatment"],
            "priority": row["priority"]
        }
        for row in rows
    ]
    return jsonify({"patients": patients}), 200


@app.route("/api/patients", methods=["POST"])
def add_patient():
    """
    Add a new patient to the database.
    Validates all fields before inserting (backend security).
    """
    data = request.get_json()

    if data is None:
        return jsonify({"errors": ["Request body must be valid JSON."]}), 400

    is_valid, errors = validate_patient_data(data)

    if not is_valid:
        return jsonify({"errors": errors}), 400

    # All validation passed — safe to insert using parameterized query
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO patients (name, diagnosis, treatment, priority) VALUES (?, ?, ?, ?)",
        (data["name"].strip(), data["diagnosis"].strip(), data["treatment"].strip(), int(data["priority"]))
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message": "Patient added successfully.",
        "patient": {
            "id": new_id,
            "name": data["name"].strip(),
            "diagnosis": data["diagnosis"].strip(),
            "treatment": data["treatment"].strip(),
            "priority": int(data["priority"])
        }
    }), 201


@app.route("/api/patients/<int:patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    """Delete a patient by id."""
    conn = get_db()
    cursor = conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"errors": [f"Patient with id {patient_id} was not found."]}), 404

    return jsonify({"message": "Patient deleted successfully."}), 200


if __name__ == "__main__":
    init_db()
    app.run(port=5001, debug=True)
