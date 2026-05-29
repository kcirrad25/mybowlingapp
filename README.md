# Cherokee Bowling League Portal

Django web application for bowling teams, bowlers, weekly scores, rankings, profile management, and admin score entry.

## Features

- Authentication with login/signup/logout
- Admin approval required for newly signed-up users before activation
- OTP-based MFA setup and verification for admin access
- Admin access restriction by allow-listed IPs or VPN egress addresses
- Protected dashboard with team rankings
- Dashboard charts for team trends and top bowler averages
- Team and individual bowler stat pages
- Admin-managed weekly score entry and handicap updates
- Audit logging for score and handicap edits
- Access request form for new users
- Admin upload for score-sheet PDFs with text extraction and Textract OCR fallback
- Editable logo and background image through admin (`SiteBranding`)

## Data Model (Normalized)

- `Team`: One team record per team name
- `Bowler`: One bowler profile, linked to one team
- `LeagueWeek`: Canonical week table (`1..20` and date)
- `BowlerScore`: One row per `(week, bowler)` with game1/2/3, handicap, scratch, total
- `TeamScore`: One row per `(week, team)` with game1/2/3, handicap, scratch, total
- `UserProfile`: One row per app user
- `AccessRequest`: Workflow table for pending/reviewed/approved requests
- `ScoreSheetUpload`: Uploaded PDF, extracted text, parsing status
- `AuditLog`: Append-only record of score creates, updates, and deletes
- `SiteBranding`: Active logo and background assets

## Local Setup

1. Install dependencies:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Copy environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

3. Run migrations:

   ```powershell
   .\.venv\Scripts\python.exe manage.py migrate
   ```

4. Create admin user:

   ```powershell
   .\.venv\Scripts\python.exe manage.py createsuperuser
   ```

5. Start server:

   ```powershell
   .\.venv\Scripts\python.exe manage.py runserver
   ```

6. Seed demo data:

   ```powershell
   .\.venv\Scripts\python.exe manage.py seed_demo_data
   ```

## PDF Import Notes

The parser currently expects CSV-like lines in extracted text:

```text
WEEK,1,2026-01-10
BOWLER,B001,120,140,130,45
TEAM,Team A,540,520,500,100
```

For non-standard scans, keep upload history in admin and refine parsing rules in `league/services.py`.

For scanned image PDFs, enable AWS Textract and then poll OCR jobs with:

```powershell
.\.venv\Scripts\python.exe manage.py process_textract_jobs
```

## AWS Hosting Guidance

Recommended deployment options:

- AWS Elastic Beanstalk: easiest managed Django deployment
- AWS ECS Fargate: containerized and scalable
- AWS RDS PostgreSQL: production database
- AWS S3 + CloudFront: media/static delivery
- AWS Textract: OCR for scanned score sheets

Environment variables to set in AWS:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` (RDS PostgreSQL URL)
- `ADMIN_ALLOWED_IPS` (office, VPN, or bastion egress IPs)
- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_REGION_NAME`
- `AWS_TEXTRACT_ENABLED`

## Security Recommendations

- Keep `DEBUG=False` in production
- Use HTTPS only, HSTS enabled
- Use strong password policy and required MFA for admin users
- Restrict admin URLs with IP allow-list or VPN egress IPs
- Run regular backups for RDS
- Review audit logs for score and handicap changes
- Consider row-level permissions if teams should only edit their own data

## Demo Access

After `seed_demo_data`, a local demo superuser is created:

- Username: `leagueadmin`
- Password: `ChangeMe123!`

Change that password immediately outside of disposable local testing.
