import flask
app = flask.Flask(__name__)
patient_info = [
    {'name': "Mike Schmidt", 'diagnosis': "Insomnia", 'treatment': "Melatonin",'priority': 2},
    {'name': "Mclovin", 'diagnosis': "Alcohol Poisoning", 'treatment': "Stomach Pump", 'priority': 5},
    {'name': "Blair Rosas", 'diagnosis': "Broken Arm", 'treatment': "Cast", 'priority': 3},
    {'name': "Erick Rowe", 'diagnosis': "Septicemia", 'treatment': "Broad-spectrum IV Antibiotics", 'priority': 4}
]
@app.route("/")
def home():
    return flask.render_template("home.html")
@app.route("/patients")
def patients():
    # Change "patients.html" to "patients_table.html"
    return flask.render_template("patients_table.html", patient_info=patient_info)