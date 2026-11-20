-- Job Application Tracker: database creation script
-- Usage:  mysql -u root -p < schema.sql
-- Requires MySQL 8.0+ (JSON columns, CHECK constraints).

CREATE DATABASE IF NOT EXISTS job_tracker;
USE job_tracker;

-- Drop in child-to-parent order so the script can be re-run safely.
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS contacts;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS companies;

CREATE TABLE companies (
    company_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry     VARCHAR(50),
    website      VARCHAR(200),
    city         VARCHAR(50),
    state        VARCHAR(50),
    notes        TEXT
);

CREATE TABLE jobs (
    job_id       INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    job_title    VARCHAR(100) NOT NULL,
    job_type     ENUM('Full-time','Part-time','Contract','Internship'),
    salary_min   INT,
    salary_max   INT,
    job_url      VARCHAR(300),
    date_posted  DATE,
    requirements JSON,              -- e.g. ["Python", "SQL", "Flask"]
    CONSTRAINT fk_jobs_company FOREIGN KEY (company_id)
        REFERENCES companies (company_id) ON DELETE CASCADE,
    CONSTRAINT chk_salary_range CHECK
        (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)
);

CREATE TABLE applications (
    application_id   INT PRIMARY KEY AUTO_INCREMENT,
    job_id           INT NOT NULL,
    application_date DATE NOT NULL,
    status           ENUM('Applied','Screening','Interview','Offer','Rejected','Withdrawn')
                     NOT NULL DEFAULT 'Applied',
    resume_version   VARCHAR(50),
    cover_letter_sent BOOLEAN NOT NULL DEFAULT FALSE,
    interview_data   JSON,          -- e.g. {"rounds": [{"type": "Phone", "date": "2026-10-05"}]}
    CONSTRAINT fk_applications_job FOREIGN KEY (job_id)
        REFERENCES jobs (job_id) ON DELETE CASCADE
);

CREATE TABLE contacts (
    contact_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title        VARCHAR(100),
    email        VARCHAR(100),
    phone        VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes        TEXT,
    CONSTRAINT fk_contacts_company FOREIGN KEY (company_id)
        REFERENCES companies (company_id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------
-- Sample data so the app has something to show on first run
-- ---------------------------------------------------------------
INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('TechCorp',   'Software',   'https://www.techcorp.example',   'Miami',   'Florida', 'Met the team at the spring career fair.'),
('DataCo',     'Analytics',  'https://www.dataco.example',     'Tampa',   'Florida', 'Hybrid, two days in office.'),
('CloudNine',  'Cloud',      'https://www.cloudnine.example',  'Austin',  'Texas',   NULL),
('HealthBridge','Healthcare','https://www.healthbridge.example','Atlanta','Georgia', 'Referral from a classmate.');

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer',  'Full-time',  70000,  90000, 'https://www.techcorp.example/jobs/101', '2026-10-01', JSON_ARRAY('Python','SQL','Flask')),
(2, 'Data Analyst',        'Full-time',  65000,  80000, 'https://www.dataco.example/jobs/22',    '2026-10-08', JSON_ARRAY('Python','SQL','Tableau')),
(3, 'Backend Intern',      'Internship', 22000,  28000, 'https://www.cloudnine.example/intern', '2026-10-12', JSON_ARRAY('Python','Git','Docker','AWS')),
(4, 'Junior Web Developer','Contract',   50000,  60000, NULL,                                   '2026-10-15', JSON_ARRAY('HTML','CSS','JavaScript','Flask')),
(1, 'QA Engineer',         'Full-time',  60000,  75000, NULL,                                   '2026-10-20', JSON_ARRAY('Python','Selenium','SQL'));

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2026-10-03', 'Interview',  'v2-software', TRUE,  JSON_OBJECT('rounds', JSON_ARRAY(JSON_OBJECT('type','Phone screen','date','2026-10-10'), JSON_OBJECT('type','Technical','date','2026-10-17')), 'notes', 'Prepare Flask and SQL examples.')),
(2, '2026-10-09', 'Screening',  'v2-data',     TRUE,  NULL),
(3, '2026-10-13', 'Applied',    'v1-general',  FALSE, NULL),
(4, '2026-10-16', 'Rejected',   'v1-general',  FALSE, NULL),
(5, '2026-10-21', 'Offer',      'v2-software', TRUE,  JSON_OBJECT('rounds', JSON_ARRAY(JSON_OBJECT('type','Onsite','date','2026-11-02')), 'notes', 'Offer expires Nov 30.'));

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Maria Lopez',  'Technical Recruiter', 'maria.lopez@techcorp.example', '305-555-0142', 'https://www.linkedin.com/in/example-maria', 'Prefers email.'),
(2, 'James Carter', 'Hiring Manager',      'j.carter@dataco.example',      '813-555-0178', NULL, NULL),
(3, 'Priya Shah',   'University Recruiter','priya.shah@cloudnine.example', NULL,           NULL, 'Sent thank-you note after career fair.'),
(4, 'Daniel Kim',   'Engineering Lead',    'daniel.kim@healthbridge.example', '404-555-0111', NULL, NULL);
