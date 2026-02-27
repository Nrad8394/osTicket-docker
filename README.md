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
open http://localhost:8080

# 5. Log in with your admin credentials from .env
#    Default: ostadmin / Adm1nP@ss!
```

That's it. Nothing else to do.

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
| `OST_HELPDESK_URL`   | Public URL of your helpdesk          | `http://localhost:8080`|
| `APP_PORT`           | Host port to expose osTicket on      | `8080`               |

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
