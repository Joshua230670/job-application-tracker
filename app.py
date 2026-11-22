# Job Application Tracker - Flask application.
import json
import os
import re
from datetime import date, datetime

import mysql.connector
from flask import Flask, abort, flash, redirect, render_template, request, url_for

from database import execute, fetch_all, fetch_one, load_json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]
STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]
ACTIVE_STATUSES = ["Applied", "Screening", "Interview"]
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ---------------------------------------------------------------------------
# Table descriptions
#
# Field types: text, textarea, int, date, email, url, select, fk, bool,
#                skills (comma list -> JSON array), json (raw JSON text)
# 
# Table and column names below are fixed in code, never taken from user input.
# ---------------------------------------------------------------------------
ENTITIES = {
    "companies": {
        "singular": "Company",
        "plural": "Companies",
        "table": "companies",
        "pk": "company_id",
        "title_key": "company_name",
        "list_sql": "SELECT * FROM companies ORDER BY company_name",
        "detail_sql": "SELECT * FROM companies WHERE company_id = %s",
        "columns": [("company_name", "Company"), ("industry", "Industry"),
                    ("city", "City"), ("state", "State")],
        "cascade_note": "This also deletes the company's jobs, their applications, and its contacts.",
        "fields": [
            {"name": "company_name", "label": "Company name", "type": "text", "required": True, "max": 100},
            {"name": "industry", "label": "Industry", "type": "text", "max": 50},
            {"name": "website", "label": "Website", "type": "url", "max": 200},
            {"name": "city", "label": "City", "type": "text", "max": 50},
            {"name": "state", "label": "State", "type": "text", "max": 50},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "related": [
            {"title": "Jobs", "entity": "jobs",
             "sql": "SELECT * FROM jobs WHERE company_id = %s ORDER BY date_posted DESC",
             "columns": [("job_title", "Title"), ("job_type", "Type"), ("date_posted", "Posted")]},
            {"title": "Contacts", "entity": "contacts",
             "sql": "SELECT * FROM contacts WHERE company_id = %s ORDER BY contact_name",
             "columns": [("contact_name", "Name"), ("title", "Title"), ("email", "Email")]},
        ],
    },
    "jobs": {
        "singular": "Job",
        "plural": "Jobs",
        "table": "jobs",
        "pk": "job_id",
        "title_key": "job_title",
        "list_sql": ("SELECT j.*, c.company_name FROM jobs j "
                     "JOIN companies c ON c.company_id = j.company_id "
                     "ORDER BY j.date_posted DESC, j.job_id DESC"),
        "detail_sql": ("SELECT j.*, c.company_name FROM jobs j "
                       "JOIN companies c ON c.company_id = j.company_id WHERE j.job_id = %s"),
        "columns": [("job_title", "Title"), ("company_name", "Company"), ("job_type", "Type"),
                    ("salary", "Salary"), ("date_posted", "Posted")],
        "cascade_note": "This also deletes every application for this job.",
        "fields": [
            {"name": "company_id", "label": "Company", "type": "fk", "required": True,
             "parent": "companies", "display": "company_name",
             "options_sql": "SELECT company_id AS value, company_name AS label FROM companies ORDER BY company_name"},
            {"name": "job_title", "label": "Job title", "type": "text", "required": True, "max": 100},
            {"name": "job_type", "label": "Job type", "type": "select", "options": JOB_TYPES},
            {"name": "salary_min", "label": "Salary minimum (USD)", "type": "int"},
            {"name": "salary_max", "label": "Salary maximum (USD)", "type": "int"},
            {"name": "job_url", "label": "Job posting URL", "type": "url", "max": 300},
            {"name": "date_posted", "label": "Date posted", "type": "date"},
            {"name": "requirements", "label": "Required skills", "type": "skills",
             "help": "Separate skills with commas, for example: Python, SQL, Flask. Job Match uses this list."},
        ],
        "related": [
            {"title": "Applications", "entity": "applications",
             "sql": "SELECT * FROM applications WHERE job_id = %s ORDER BY application_date DESC",
             "columns": [("application_date", "Applied"), ("status", "Status"), ("resume_version", "Resume")]},
        ],
    },
    "applications": {
        "singular": "Application",
        "plural": "Applications",
        "table": "applications",
        "pk": "application_id",
        "title_key": "job_title",
        "list_sql": ("SELECT a.*, j.job_title, c.company_name FROM applications a "
                     "JOIN jobs j ON j.job_id = a.job_id "
                     "JOIN companies c ON c.company_id = j.company_id "
                     "ORDER BY a.application_date DESC, a.application_id DESC"),
        "detail_sql": ("SELECT a.*, j.job_title, c.company_name FROM applications a "
                       "JOIN jobs j ON j.job_id = a.job_id "
                       "JOIN companies c ON c.company_id = j.company_id WHERE a.application_id = %s"),
        "columns": [("job_title", "Job"), ("company_name", "Company"), ("application_date", "Applied"),
                    ("status", "Status"), ("resume_version", "Resume")],
        "cascade_note": "",
        "fields": [
            {"name": "job_id", "label": "Job", "type": "fk", "required": True,
             "parent": "jobs", "display": "job_title",
             "options_sql": ("SELECT j.job_id AS value, CONCAT(j.job_title, ' at ', c.company_name) AS label "
                             "FROM jobs j JOIN companies c ON c.company_id = j.company_id ORDER BY label")},
            {"name": "application_date", "label": "Application date", "type": "date", "required": True,
             "default": "today"},
            {"name": "status", "label": "Status", "type": "select", "required": True,
             "options": STATUSES, "default": "Applied"},
            {"name": "resume_version", "label": "Resume version", "type": "text", "max": 50},
            {"name": "cover_letter_sent", "label": "Cover letter sent", "type": "bool"},
            {"name": "interview_data", "label": "Interview details (JSON)", "type": "json",
             "help": 'Optional. Example: {"rounds": [{"type": "Phone", "date": "2026-10-05"}], "notes": "Ask about team size"}'},
        ],
        "related": [],
    },
    "contacts": {
        "singular": "Contact",
        "plural": "Contacts",
        "table": "contacts",
        "pk": "contact_id",
        "title_key": "contact_name",
        "list_sql": ("SELECT ct.*, c.company_name FROM contacts ct "
                     "JOIN companies c ON c.company_id = ct.company_id ORDER BY ct.contact_name"),
        "detail_sql": ("SELECT ct.*, c.company_name FROM contacts ct "
                       "JOIN companies c ON c.company_id = ct.company_id WHERE ct.contact_id = %s"),
        "columns": [("contact_name", "Name"), ("title", "Title"), ("company_name", "Company"),
                    ("email", "Email"), ("phone", "Phone")],
        "cascade_note": "",
        "fields": [
            {"name": "company_id", "label": "Company", "type": "fk", "required": True,
             "parent": "companies", "display": "company_name",
             "options_sql": "SELECT company_id AS value, company_name AS label FROM companies ORDER BY company_name"},
            {"name": "contact_name", "label": "Name", "type": "text", "required": True, "max": 100},
            {"name": "title", "label": "Job title", "type": "text", "max": 100},
            {"name": "email", "label": "Email", "type": "email", "max": 100},
            {"name": "phone", "label": "Phone", "type": "text", "max": 20},
            {"name": "linkedin_url", "label": "LinkedIn URL", "type": "url", "max": 200},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "related": [],
    },
}

# Flask URL converter that only matches the four table names.
ENTITY = "<any({}):entity_key>".format(",".join(ENTITIES))


@app.template_filter("pretty_json")
def pretty_json(value):
    return json.dumps(value, indent=2, ensure_ascii=False)


@app.context_processor
def inject_globals():
    return {"entities": ENTITIES}


@app.errorhandler(mysql.connector.Error)
def database_error(err):
    # Show a readable page when MySQL is down or misconfigured.
    return render_template("error.html", message=str(err)), 500


# ---------------------------------------------------------------------------
# Helpers: formatting, validation, saving
# ---------------------------------------------------------------------------
def format_salary(low, high):
    if low is None and high is None:
        return None
    if low is not None and high is not None:
        return f"${low:,} - ${high:,}"
    return f"${(low if low is not None else high):,}"


def decorate(row):
    # Parse JSON columns and add display-only fields to a database row.
    row = dict(row)
    for key in ("requirements", "interview_data"):
        if key in row:
            row[key] = load_json(row[key])
    if "salary_min" in row:
        row["salary"] = format_salary(row["salary_min"], row["salary_max"])
    return row


def convert(field, raw):
    # Validate one non-empty form value and return the value to store.
    ftype = field["type"]
    if ftype in ("text", "textarea", "email", "url"):
        if field.get("max") and len(raw) > field["max"]:
            raise ValueError(f"must be at most {field['max']} characters")
        if ftype == "email" and not EMAIL_PATTERN.match(raw):
            raise ValueError("must be a valid email address")
        if ftype == "url" and not re.match(r"^https?://\S+$", raw):
            raise ValueError("must start with http:// or https://")
        return raw
    if ftype == "int":
        number = int(raw)  # int() raises ValueError for non-numbers
        if number < 0:
            raise ValueError("cannot be negative")
        return number
    if ftype == "fk":
        return int(raw)
    if ftype == "date":
        return datetime.strptime(raw, "%Y-%m-%d").date()
    if ftype == "select":
        if raw not in field["options"]:
            raise ValueError("must be one of the listed options")
        return raw
    if ftype == "skills":
        skills = []
        for part in re.split(r"[,;\n]", raw):
            part = re.sub(r"\s+", " ", part).strip()
            if part and part.lower() not in [s.lower() for s in skills]:
                skills.append(part)
        return json.dumps(skills) if skills else None
    if ftype == "json":
        return json.dumps(json.loads(raw))  # json.loads raises ValueError if invalid
    raise ValueError("unsupported field type")


def parse_form(entity, form):
    # Validate submitted form data. Returns (values_to_store, error_messages).
    values, errors = {}, []
    for field in entity["fields"]:
        name, label = field["name"], field["label"]
        if field["type"] == "bool":
            values[name] = 1 if form.get(name) else 0
            continue
        raw = (form.get(name) or "").strip()
        if not raw:
            values[name] = None
            if field.get("required"):
                errors.append(f"{label} is required.")
            continue
        try:
            values[name] = convert(field, raw)
        except ValueError as err:
            message = str(err)
            if field["type"] == "int" and "invalid literal" in message:
                message = "must be a whole number"
            elif field["type"] == "date":
                message = "must be a valid date"
            elif field["type"] == "json":
                message = "is not valid JSON"
            errors.append(f"{label} {message}.")
    low, high = values.get("salary_min"), values.get("salary_max")
    if low is not None and high is not None and low > high:
        errors.append("Salary minimum cannot be greater than salary maximum.")
    return values, errors


def form_value(field, stored):
    # Convert a stored value into text for an edit form.
    if stored is None:
        return ""
    if field["type"] == "skills":
        return ", ".join(stored) if isinstance(stored, list) else ""
    if field["type"] == "json":
        return json.dumps(stored, indent=2)
    if field["type"] == "date":
        return stored.isoformat()
    return stored


def initial_values(entity, record):
    values = {}
    for field in entity["fields"]:
        if record is not None:
            values[field["name"]] = form_value(field, record[field["name"]])
        elif field.get("default") == "today":
            values[field["name"]] = date.today().isoformat()
        else:
            values[field["name"]] = field.get("default", "")
    return values


def load_options(entity):
    # Dropdown choices for foreign-key fields, keyed by field name.
    return {f["name"]: fetch_all(f["options_sql"]) for f in entity["fields"] if f["type"] == "fk"}


def save(entity, values, record_id):
    columns = list(values)
    if record_id is None:
        placeholders = ", ".join(["%s"] * len(columns))
        sql = f"INSERT INTO {entity['table']} ({', '.join(columns)}) VALUES ({placeholders})"
        return execute(sql, tuple(values.values()))
    assignments = ", ".join(f"{column} = %s" for column in columns)
    sql = f"UPDATE {entity['table']} SET {assignments} WHERE {entity['pk']} = %s"
    execute(sql, (*values.values(), record_id))
    return record_id


def get_record_or_404(entity, record_id):
    row = fetch_one(entity["detail_sql"], (record_id,))
    if row is None:
        abort(404)
    return decorate(row)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/")
def dashboard():
    counts = fetch_one(
        "SELECT (SELECT COUNT(*) FROM companies) AS companies, "
        "(SELECT COUNT(*) FROM jobs) AS jobs, "
        "(SELECT COUNT(*) FROM applications) AS applications, "
        "(SELECT COUNT(*) FROM contacts) AS contacts"
    )
    by_status = {row["status"]: row["count"] for row in fetch_all(
        "SELECT status, COUNT(*) AS count FROM applications GROUP BY status")}
    total = counts["applications"]
    status_rows = [(s, by_status.get(s, 0)) for s in STATUSES]
    stats = {
        "active": sum(by_status.get(s, 0) for s in ACTIVE_STATUSES),
        "interviews": by_status.get("Interview", 0),
        "offers": by_status.get("Offer", 0),
        "rejected": by_status.get("Rejected", 0),
        # Share of applications that moved past "Applied" or were answered with a rejection.
        "response_rate": round(100 * sum(by_status.get(s, 0) for s in
                                         ("Screening", "Interview", "Offer", "Rejected")) / total) if total else 0,
    }
    recent = fetch_all(
        "SELECT a.application_id, a.application_date, a.status, j.job_title, c.company_name "
        "FROM applications a JOIN jobs j ON j.job_id = a.job_id "
        "JOIN companies c ON c.company_id = j.company_id "
        "ORDER BY a.application_date DESC, a.application_id DESC LIMIT 5")
    return render_template("dashboard.html", counts=counts, stats=stats,
                           status_rows=status_rows, total=total, recent=recent)


# ---------------------------------------------------------------------------
# Generic CRUD routes (companies, jobs, applications, contacts)
# ---------------------------------------------------------------------------
@app.route(f"/{ENTITY}")
def list_view(entity_key):
    entity = ENTITIES[entity_key]
    rows = [decorate(row) for row in fetch_all(entity["list_sql"])]
    return render_template(f"{entity_key}.html", entity=entity, key=entity_key, rows=rows)


@app.route(f"/{ENTITY}/<int:record_id>")
def detail_view(entity_key, record_id):
    entity = ENTITIES[entity_key]
    record = get_record_or_404(entity, record_id)
    related = [{**rel, "rows": [decorate(r) for r in fetch_all(rel["sql"], (record_id,))]}
               for rel in entity["related"]]
    return render_template("detail.html", entity=entity, key=entity_key, record=record, related=related)


def handle_form(entity_key, record_id=None):
    entity = ENTITIES[entity_key]
    record = get_record_or_404(entity, record_id) if record_id else None
    options = load_options(entity)

    # A job needs a company, an application needs a job, and so on.
    for field in entity["fields"]:
        if field["type"] == "fk" and not options[field["name"]]:
            parent = ENTITIES[field["parent"]]
            flash(f"Add a {parent['singular'].lower()} first, then come back to add this {entity['singular'].lower()}.", "warning")
            return redirect(url_for("new_view", entity_key=field["parent"]))

    if request.method == "POST":
        values, errors = parse_form(entity, request.form)
        if not errors:
            try:
                saved_id = save(entity, values, record_id)
            except mysql.connector.Error as err:
                errors.append(f"The database rejected this entry: {err.msg}")
            else:
                verb = "updated" if record_id else "added"
                flash(f"{entity['singular']} {verb}.", "success")
                return redirect(url_for("detail_view", entity_key=entity_key, record_id=saved_id))
        for message in errors:
            flash(message, "danger")
        form_values = {f["name"]: request.form.get(f["name"], "") for f in entity["fields"]}
    else:
        form_values = initial_values(entity, record)

    return render_template("form.html", entity=entity, key=entity_key, record=record,
                           values=form_values, options=options)


@app.route(f"/{ENTITY}/new", methods=["GET", "POST"])
def new_view(entity_key):
    return handle_form(entity_key)


@app.route(f"/{ENTITY}/<int:record_id>/edit", methods=["GET", "POST"])
def edit_view(entity_key, record_id):
    return handle_form(entity_key, record_id)


@app.route(f"/{ENTITY}/<int:record_id>/delete", methods=["GET", "POST"])
def delete_view(entity_key, record_id):
    # GET shows a confirmation page; POST performs the delete.
    entity = ENTITIES[entity_key]
    record = get_record_or_404(entity, record_id)
    if request.method == "POST":
        execute(f"DELETE FROM {entity['table']} WHERE {entity['pk']} = %s", (record_id,))
        flash(f"{entity['singular']} deleted.", "success")
        return redirect(url_for("list_view", entity_key=entity_key))
    return render_template("confirm_delete.html", entity=entity, key=entity_key, record=record)


# ---------------------------------------------------------------------------
# Job Match
# ---------------------------------------------------------------------------
def normalize_skill(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def parse_skills(text):
    # Split 'Python, SQL; Flask' into {normalized: as typed}, without duplicates.
    skills = {}
    for part in re.split(r"[,;\n]", text or ""):
        key = normalize_skill(part)
        if key and key not in skills:
            skills[key] = part.strip()
    return skills


def match_jobs(user_skills, jobs):
    """
    Rank jobs by the share of their required skills the user has.

    user_skills: {normalized skill: display text}
    jobs: rows containing job_id, job_title, company_name and requirements (JSON).
    Jobs with no listed requirements are skipped because no percentage exists.
    """
    results = []
    for job in jobs:
        requirements = load_json(job["requirements"])
        if not isinstance(requirements, list):
            continue
        required = {}
        for item in requirements:
            key = normalize_skill(item)
            if key and key not in required:
                required[key] = str(item).strip()
        if not required:
            continue
        matched = [shown for key, shown in required.items() if key in user_skills]
        missing = [shown for key, shown in required.items() if key not in user_skills]
        results.append({
            "job_id": job["job_id"],
            "job_title": job["job_title"],
            "company_name": job["company_name"],
            "percent": int(100 * len(matched) / len(required) + 0.5),
            "matched": matched,
            "missing": missing,
            "total": len(required),
        })
    results.sort(key=lambda r: (-r["percent"], -len(r["matched"]), r["job_title"].lower()))
    return results


@app.route("/job-match")
def job_match():
    skills_text = request.args.get("skills", "").strip()
    jobs = fetch_all("SELECT j.job_id, j.job_title, j.requirements, c.company_name FROM jobs j "
                     "JOIN companies c ON c.company_id = j.company_id")
    known_skills = sorted({str(s).strip() for j in jobs
                           for s in (load_json(j["requirements"]) or []) if str(s).strip()},
                          key=str.lower)
    user_skills = parse_skills(skills_text)
    results = match_jobs(user_skills, jobs) if user_skills else None
    return render_template("job_match.html", skills_text=skills_text, user_skills=user_skills,
                           results=results, known_skills=known_skills)


if __name__ == "__main__":
    app.run(debug=True)
