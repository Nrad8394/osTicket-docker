# osTicket v1.18.3 — Fully Automated Docker Stack

100% plug-and-play. Run `docker-compose up` and osTicket is installed,
configured, and ready to use. No browser setup wizard. No manual steps.
Fully reproducible across any VM.

---

## How it Works

On **first boot**, the container automatically:
1. Waits for MySQL to be ready
2. Writes `ost-config.php` with your DB credentials
3. Runs the osTicket CLI installer (`setup/cli/manage.php`)
4. Falls back to direct SQL install if CLI fails
5. Creates your admin account
6. Removes the `/setup` directory (security)
7. Locks the config file
8. Writes an `.installed` flag so it skips all this on restarts
9. Starts cron + Apache

On **subsequent boots**, it just starts cron + Apache instantly.

---

## Folder Structure

```
osticket-docker/
├── Dockerfile
├── docker-compose.yml
├── .env.example                ← copy to .env and fill in
├── config/
│   ├── apache-osticket.conf
│   └── php-osticket.ini
├── scripts/
│   └── entrypoint.sh
└── osTicket-v1.18.3/
    └── upload/                 ← your osTicket source files
```

---

## Quick Start

```bash
# 1. Set your configuration
cp .env.example .env
nano .env          # set your passwords, domain, admin details

# 2. Build and launch
docker-compose up -d --build

# 3. Watch the automated install
docker-compose logs -f osticket
# Wait for: ✓ INSTALLATION COMPLETE

# 4. Open your browser
open http://localhost:8082

# 5. Log in with admin credentials
# Initial admin: ostadmin / Adm1nP@ss! (from .env)
# After seeding: sadmin / AdminSecurePass123! (configured in seeder/data/staff.json)
# See "Database Seeding" section below for details
```

That's it. Nothing else to do.

---

## Database Seeding (Production Data)

After the initial Docker setup, you can populate osTicket with production-ready data using the Python seeding system in the `seeder/` directory.

### What Gets Seeded

The seeder populates your osTicket instance with:
- **12 Staff Accounts** with bcrypt-hashed passwords (agents, supervisors, managers)
- **8 Departments** (BAS, BSD, ICT, Legal, Customer Service, HR, Finance, Admin)
- **7 Teams** (Desktop Support, Network Team, Security Team, Development, Help Desk, Field Ops, Management)
- **10 SLA Plans** (Business-critical to routine, with appropriate response times)
- **10 Staff Roles** with permission matrices
- **83 Help Topics** with intelligent routing (auto-assigns based on issue type and severity)
- **16 Custom Ticket Statuses** (beyond default Open/Closed)
- **12 Ticket Filters** for auto-assignment and notifications
- **5 Custom Lists** with 150+ predefined items (Priority Levels, Issue Types, etc.)
- **26 Custom Form Fields** for structured data collection

### Running the Seeder

```bash
# Navigate to seeder directory
cd seeder

# Create Python virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# OR: source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure database connection
# The seeder automatically reads from the root .env file
# No need for a separate seeder/.env (though you can create one if desired)

# Run the seeder (recommended: full mode with backup)
python main.py --mode full --backup --verbose
```

### Seeding Modes

- **`--mode full`**: INSERT or UPDATE all records (non-destructive, recommended)
- **`--mode partial`**: INSERT IGNORE (skips existing records, safest)
- **`--mode validate`**: Check readiness without making changes

### Important Notes

⚠️ **Admin Account**: The seeder will update `staff_id=1` (the admin account) with credentials from `seeder/data/staff.json`:
- Username: `sadmin`
- Email: `admin@kra.gov`  
- Password: `AdminSecurePass123!`

To preserve your original admin account from `.env`, edit `seeder/data/staff.json` and remove the first entry (id=1) before running the seeder.

✅ **Data Safety**: All seeding operations use `INSERT ... ON DUPLICATE KEY UPDATE` patterns - existing data is preserved and only updated where specified. No destructive DELETE operations are performed.

📖 **Full Documentation**: See [seeder/README.md](seeder/README.md) for complete details on customization, data files, and troubleshooting.

---

## Deploying to a New VM

```bash
# Copy the entire folder to the new VM
scp -r osticket-docker/ user@new-vm:/opt/osticket/

# SSH in and start
ssh user@new-vm
cd /opt/osticket
cp .env.example .env    # or copy your existing .env
docker-compose up -d --build
```

The MySQL data is stored in a named Docker volume (`osticket_mysql_data`).
A fresh VM gets a fresh install. To **migrate data**, see the backup section below.

---

## Configuration Reference

All settings live in `.env`. Edit before first boot:

| Variable             | Description                          | Default              |
|----------------------|--------------------------------------|----------------------|
| `MYSQL_ROOT_PASSWORD`| MySQL root password                  | `R00tS3cur3Pass!`    |
| `MYSQL_DATABASE`     | Database name                        | `osticket`           |
| `MYSQL_USER`         | DB user for osTicket                 | `osticket`           |
| `MYSQL_PASSWORD`     | DB user password                     | `0sT1ck3tPass!`      |
| `MYSQL_PREFIX`       | Table prefix                         | `ost_`               |
| `OST_ADMIN_EMAIL`    | Admin account email                  | `admin@example.com`  |
| `OST_ADMIN_FNAME`    | Admin first name                     | `Admin`              |
| `OST_ADMIN_LNAME`    | Admin last name                      | `User`               |
| `OST_ADMIN_USER`     | Admin username (for login)           | `ostadmin`           |
| `OST_ADMIN_PASS`     | Admin password (for login)           | `Adm1nP@ss!`         |
| `OST_SITE_NAME`      | Helpdesk display name                | `Support Center`     |
| `OST_SITE_EMAIL`     | Default sender email                 | `support@example.com`|
| `OST_HELPDESK_URL`   | Public URL of your helpdesk          | `http://localhost:8082`|
| `APP_PORT`           | Host port to expose osTicket on      | `8082`               |

---

## Useful Commands

```bash
# View live logs
docker-compose logs -f osticket
docker-compose logs -f mysql

# Stop the stack
docker-compose down

# Restart just the app (DB keeps running)
docker-compose restart osticket

# Shell into the app container
docker exec -it osticket_app bash

# Shell into the DB container
docker exec -it osticket_db mysql -u osticket -p0sT1ck3tPass! osticket

# Check install flag
docker exec osticket_app cat /var/www/html/.installed
```

---

## Backup & Restore

### Backup database
```bash
docker exec osticket_db mysqldump \
  -u osticket -p0sT1ck3tPass! osticket \
  > backup-$(date +%Y%m%d).sql
```

### Restore database
```bash
docker exec -i osticket_db mysql \
  -u osticket -p0sT1ck3tPass! osticket \
  < backup-20240101.sql
```

### Backup attachments
```bash
docker cp osticket_app:/var/www/html/attachments ./attachments-backup
```

### Migrate to a new VM with existing data
```bash
# On old VM — export DB and attachments
docker exec osticket_db mysqldump -u osticket -p0sT1ck3tPass! osticket > osticket.sql
docker cp osticket_app:/var/www/html/attachments ./attachments

# On new VM — start stack, then restore
docker-compose up -d --build
sleep 20    # wait for MySQL to be ready
docker exec -i osticket_db mysql -u osticket -p0sT1ck3tPass! osticket < osticket.sql
docker cp ./attachments osticket_app:/var/www/html/attachments
docker exec osticket_app touch /var/www/html/.installed   # skip re-install
docker-compose restart osticket
```

---

## Resetting to a Clean Install

```bash
# Full reset — destroys all data
docker-compose down -v
docker-compose up -d --build
```

---

## Troubleshooting

**Container keeps restarting**
```bash
docker-compose logs osticket
```

**Install fails / blank page**
```bash
# Check PHP errors
docker exec osticket_app tail -50 /var/log/apache2/php_errors.log
docker exec osticket_app tail -50 /var/log/apache2/osticket_error.log
```

**Database connection refused**
```bash
# Check MySQL is healthy
docker inspect osticket_db | grep -A5 Health
```

**Want to re-run the installer**
```bash
docker exec osticket_app rm /var/www/html/.installed
docker-compose restart osticket
```
