# Job Application Tracker 
A web application to help track job applications during the job search process. 

## Features (Coming Soon) 
- Track companies and job listings 
- Record application submissions 
- Manage interview schedules 
- Store contact information 

## Technologies 
- MySQL Database 
- Python with Flask 
- HTML/CSS for the web interface 

## Setup
1. Clone the repository
2. Run the command in the terminal:
   ```Get-Content schema.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p```
3. When prompted, enter your database password.
4. In database.py, add the password to the get_db() function on line 12, right beside "DB_PASSWORD".
5. Run app.py and click the webpage (https://127.0.0.1:5000) in the terminal.

## Project Structure
```
job_tracker/
├── app.py            # Main Flask application
├── database.py       # Database connection functions
├── schema.sql        # Database creation script
├── templates/        # HTML templates
│     ├── base.html
│     ├── dashboard.html
│     ├── companies.html
│     ├── jobs.html
│     ├── applications.html
│     ├── contacts.html
│     ├── form.html
│     ├── error.html
│     ├── detail.html
│     ├── confirm_delete.html
│     ├── _macros.html
│     └── job_match.html
├── static/           # CSS, images
│     └──style.css
├── README.md         # Project description
├── AI_USAGE.md       # GenAI documentation
└── requirements.txt  # Python dependencies
```

## Database
| Table | Key columns |
| --- | --- |
| `companies` | company_id, company_name, industry, website, city, state, notes |
| `jobs` | job_id, company_id (FK), job_title, job_type, salary_min/max, job_url, date_posted, requirements (JSON) |
| `applications` | application_id, job_id (FK), application_date, status, resume_version, cover_letter_sent, interview_data (JSON) |
| `contacts` | contact_id, company_id (FK), contact_name, title, email, phone, linkedin_url, notes |

Deleting a company also deletes its jobs, applications and contacts (`ON DELETE CASCADE`); the delete
confirmation page says so before anything is removed.
