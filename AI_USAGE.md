# AI Usage Documentation

## Tools Used
- Claude: Debugging, code review, and polishing of the front-end development.

## Key Prompts
- "What are the steps I can take to set up a database with MySQL."
- "How do I turn a JSON column into Python data?"
- "Can you create the HTML templates for what each page could look like?"
- "Can you help me develop the functionality of the front-end with Flask?"
- "How do I set up the requirements.txt?"
- "How do I export a MySQL Workbench schema into a .sql file that can be read by Python?"
- "How can I get Python to read my schema.sql file?"
- "I'm supposed to develop a job match feature that matches the user's skill, with the ones required by the company. This has to be measured through a percentage. How can I accomplish this?"

## What Worked Well
- AI generated the web pages with no issue.
- Described easily the steps I needed to take to develop the functionality for program.
- Helped me understand the error messages.
- Showed me how to convert JSON into a readable format for Python.
- Formatted my code into a more readable format and added comments to make sections of the code more understandable.
- Made comments on the code that were easy to follow.

## What the AI Could Not Do
- N/A

## What I Modified
- Changed how the job match skills were calculated by adding the percentage to be displayed rather than just a fraction.
- Rather than using the instruction '<' to load 'schema.sql', I used 'Get-Content schema.sql | mysql.exe -u root -p' since powershell doesn't support the original method.
- Modified the fonts and color palette in style.css to fit my own liking.
- Added a filter option in the applications page.
- Added keywords to the tables to prevent any errors (e.g., 'NOT NULL' in the job table so a job can't exist without a company, 'CHECK' so the 'salary_min' doesn't exceed 'salary_max'.

## Lessons Learned
- AI can be an incredibly useful tool to learn how certain components work, such as understanding the HTML/CSS files.
- It is incredibly detailed in explaining parts of the code it programmed that I could not understand.
- It provided a great step-by-step process to help me understand what I'm implementing.
