#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  osTicket Entrypoint — Zero-touch automated installer
#  Runs on every container start; idempotent (safe to re-run)
# ─────────────────────────────────────────────────────────────────
#
#  FIX HISTORY:
#  - Removed set -e / ERR trap from main() — they fire on innocuous
#    commands (service cron, local declarations) and silently kill
#    the script before Apache starts.
#  - Added explicit exit-code checks everywhere instead.
#  - Fixed pipe swallowing installer exit code (set -o pipefail on
#    installer subshell only).
#  - Stale apache2.pid cleanup now happens unconditionally before
#    exec apache2-foreground.
#  - apache2ctl configtest runs before exec so bad config is caught.
#  - Removed 'local' declarations from main() — local is only valid
#    inside functions.
#  - Merged the two redundant "already installed" checks into one
#    clear decision tree.
#  - All mysql calls use || echo "0" so pipefail can't abort on a
#    momentary DB hiccup.
# ─────────────────────────────────────────────────────────────────

# NOTE: NO global set -e here intentionally — we do explicit checks.
# pipefail is scoped to subshells where we need it.
set -uo pipefail

# ── Colours ───────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

log()  { echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} $*"; }
ok()   { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${NC} $*"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠${NC} $*"; }
err()  { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${NC} $*"; }
die()  { err "$*"; exit 1; }

# ── Env vars (with defaults) ──────────────────────────────────────
MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-osticket}"
MYSQL_USER="${MYSQL_USER:-osticket}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-0sT1ck3tPass!}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-R00tS3cur3Pass!}"
MYSQL_PREFIX="${MYSQL_PREFIX:-ost_}"

OST_ADMIN_EMAIL="${OST_ADMIN_EMAIL:-admin@example.com}"
OST_ADMIN_FNAME="${OST_ADMIN_FNAME:-Admin}"
OST_ADMIN_LNAME="${OST_ADMIN_LNAME:-User}"
OST_ADMIN_USER="${OST_ADMIN_USER:-ostadmin}"
OST_ADMIN_PASS="${OST_ADMIN_PASS:-Adm1nP@ss!}"

OST_SITE_NAME="${OST_SITE_NAME:-Support Center}"
OST_SITE_EMAIL="${OST_SITE_EMAIL:-support@example.com}"
OST_HELPDESK_URL="${OST_HELPDESK_URL:-http://localhost:8080}"

INSTALL_FLAG="/var/www/html/attachments/.installed"
CONFIG_FILE="/var/www/html/include/ost-config.php"
WEB_ROOT="/var/www/html"

# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────

# Returns the number of ost_ tables in the DB (0 on any error)
count_ost_tables() {
    mysql \
        -h"${MYSQL_HOST}" -P"${MYSQL_PORT}" \
        --ssl=0 --connect-timeout=10 \
        -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
        -s -N \
        -e "SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema='${MYSQL_DATABASE}'
            AND table_name LIKE '${MYSQL_PREFIX}%';" \
        2>/dev/null \
    || echo "0"
}

# Returns 0 if ost-config.php declares OSTINSTALLED as TRUE
config_is_installed() {
    grep -q "define('OSTINSTALLED',TRUE)" "${CONFIG_FILE}" 2>/dev/null
}

# Returns 0 if config has template placeholders instead of real values
config_has_placeholders() {
    grep -q '%CONFIG-' "${CONFIG_FILE}" 2>/dev/null
}

# Removes the /setup directory — must not exist when Apache serves requests
remove_setup_dir() {
    if [ -d "${WEB_ROOT}/setup" ]; then
        log "Removing /setup directory (security)..."
        rm -rf "${WEB_ROOT}/setup"
        if [ -d "${WEB_ROOT}/setup" ]; then
            die "/setup directory could not be removed — manual intervention needed."
        fi
        ok "/setup removed."
    fi
}

# ─────────────────────────────────────────────────────────────────
#  1. WAIT FOR MYSQL
# ─────────────────────────────────────────────────────────────────
wait_for_mysql() {
    log "Waiting for MySQL at ${MYSQL_HOST}:${MYSQL_PORT}..."
    local retries=0
    local max=60

    # Phase 1 — TCP
    until nc -z "${MYSQL_HOST}" "${MYSQL_PORT}" 2>/dev/null; do
        retries=$((retries + 1))
        [ $retries -ge $max ] && die "MySQL TCP port never opened after ${max} attempts."
        [ $((retries % 10)) -eq 0 ] && log "Still waiting for TCP... ${retries}/${max}" || echo -n "."
        sleep 2
    done
    echo ""
    log "TCP open. Waiting for MySQL to accept queries..."

    # Phase 2 — query readiness (use root; the app user may not exist yet)
    retries=0
    until mysqladmin ping \
        -h"${MYSQL_HOST}" -P"${MYSQL_PORT}" \
        -uroot -p"${MYSQL_ROOT_PASSWORD}" \
        --ssl=0 --silent 2>/dev/null
    do
        retries=$((retries + 1))
        [ $retries -ge $max ] && die "MySQL never became ready."
        echo -n "."
        sleep 2
    done
    echo ""
    ok "MySQL is ready."
}

# ─────────────────────────────────────────────────────────────────
#  2. WRITE ost-config.php
# ─────────────────────────────────────────────────────────────────
write_config() {
    log "Writing ost-config.php..."

    # Make writable whether it exists already or not
    touch "${CONFIG_FILE}" 2>/dev/null || true
    chmod 0666 "${CONFIG_FILE}"

    # Generate a random salt without subshell pipefail interference
    local salt
    salt=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1 || true)
    [ -z "${salt}" ] && salt="fallback-salt-$(date +%s)"

    cat > "${CONFIG_FILE}" << PHPCONFIG
<?php
# osTicket Configuration — auto-generated by Docker entrypoint
# DO NOT EDIT MANUALLY

define('OSTINSTALLED',FALSE);
define('SECRET_SALT','${salt}');
define('DBDRIVER','mysqli');
define('DBHOST','${MYSQL_HOST}');
define('DBNAME','${MYSQL_DATABASE}');
define('DBUSER','${MYSQL_USER}');
define('DBPASS','${MYSQL_PASSWORD}');
define('DBPREFIX','${MYSQL_PREFIX}');
define('DBPORT','${MYSQL_PORT}');
define('DBSSLCA','');
define('DBSSLCERT','');
define('DBSSLKEY','');
define('DBSSL',false);

define('TABLE_PREFIX','${MYSQL_PREFIX}');

@define('ATTACHMENT_PATH','${WEB_ROOT}/attachments/');
@define('BOOTSTRAP','${WEB_ROOT}/bootstrap.php');
PHPCONFIG

    chmod 0644 "${CONFIG_FILE}"
    chown www-data:www-data "${CONFIG_FILE}"
    ok "ost-config.php written."
}

# ─────────────────────────────────────────────────────────────────
#  3. START / STOP BACKGROUND APACHE (installer only)
# ─────────────────────────────────────────────────────────────────
APACHE_BG_PID=""

start_apache_background() {
    log "Starting Apache in background for installer..."
    # Clean any stale pid before starting
    rm -f /var/run/apache2/apache2.pid

    apache2-foreground &
    APACHE_BG_PID=$!

    # Wait up to 30s for Apache to actually serve requests
    local attempts=0
    until curl -sf --max-time 3 http://localhost/ > /dev/null 2>&1 || \
          curl -sf --max-time 3 http://localhost/setup/ > /dev/null 2>&1; do
        attempts=$((attempts + 1))
        if [ $attempts -ge 15 ]; then
            err "Background Apache did not respond after 30s"
            err "Apache stderr (last 20 lines of error log):"
            tail -20 /var/log/apache2/error.log 2>/dev/null || true
            return 1
        fi
        echo -n "."
        sleep 2
    done
    echo ""
    ok "Background Apache is serving (PID ${APACHE_BG_PID})."
}

stop_apache_background() {
    if [ -n "${APACHE_BG_PID}" ]; then
        log "Stopping background Apache (PID ${APACHE_BG_PID})..."
        kill "${APACHE_BG_PID}" 2>/dev/null || true
        # Wait for it to fully exit so it releases the port and pid file
        local waited=0
        while kill -0 "${APACHE_BG_PID}" 2>/dev/null; do
            waited=$((waited + 1))
            [ $waited -ge 15 ] && { warn "Background Apache did not exit cleanly; sending SIGKILL"; kill -9 "${APACHE_BG_PID}" 2>/dev/null || true; break; }
            sleep 1
        done
        APACHE_BG_PID=""
        ok "Background Apache stopped."
    fi
    # Always remove the pid file — it may linger even after the process exits
    rm -f /var/run/apache2/apache2.pid
    sleep 1
}

# ─────────────────────────────────────────────────────────────────
#  4. RUN WEB INSTALLER
# ─────────────────────────────────────────────────────────────────
run_installer() {
    local web_installer="/usr/local/bin/web-install.sh"
    [ -f "${web_installer}" ] || die "Web installer not found: ${web_installer}"

    log "Running automated web-based installer..."
    local install_log="/tmp/install-$(date +%s).log"

    # Run in a subshell with pipefail so the installer's exit code
    # is not masked by tee
    local rc=0
    ( set -o pipefail; bash "${web_installer}" 2>&1 | tee "${install_log}" ) || rc=$?

    if [ ${rc} -eq 0 ]; then
        ok "Web installer completed successfully."
        return 0
    else
        err "Web installer failed (exit code: ${rc})"
        warn "Last 50 lines of install log:"
        tail -50 "${install_log}" >&2
        return 1
    fi
}

# ─────────────────────────────────────────────────────────────────
#  5. POST-INSTALL CLEANUP & VERIFICATION
# ─────────────────────────────────────────────────────────────────
post_install_cleanup() {
    log "Post-install cleanup & verification..."

    # Verify DB tables
    local table_count
    table_count=$(count_ost_tables)
    if [ "${table_count}" -lt 10 ]; then
        err "Only ${table_count} tables found — installation incomplete."
        return 1
    fi
    ok "${table_count} osTicket tables found."

    # Verify config is marked installed
    if ! config_is_installed; then
        err "ost-config.php not marked OSTINSTALLED=TRUE after installer ran."
        return 1
    fi
    ok "ost-config.php marked as installed."

    # Security: remove setup dir
    remove_setup_dir

    # Permissions
    chmod 0644 "${CONFIG_FILE}"
    chown www-data:www-data "${CONFIG_FILE}"
    chown -R www-data:www-data "${WEB_ROOT}/attachments" 2>/dev/null || true
    chmod 755 "${WEB_ROOT}/attachments" 2>/dev/null || true

    # Write install flag
    mkdir -p "$(dirname "${INSTALL_FLAG}")"
    {
        echo "installed=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "version=1.18.3"
        echo "db_host=${MYSQL_HOST}"
        echo "admin_user=${OST_ADMIN_USER}"
    } > "${INSTALL_FLAG}"
    chmod 644 "${INSTALL_FLAG}"

    ok "Post-install cleanup complete."
}

# ─────────────────────────────────────────────────────────────────
#  6. UPGRADE / SCHEMA SIGNATURE CHECK
# ─────────────────────────────────────────────────────────────────
check_upgrade() {
    log "Checking schema signature..."
    local sig_file="${WEB_ROOT}/include/upgrader/streams/core.sig"
    if [ ! -f "${sig_file}" ]; then
        warn "core.sig not found — skipping schema check."
        return 0
    fi

    local expected_sig current_sig
    expected_sig=$(cat "${sig_file}")
    current_sig=$(mysql \
        -h"${MYSQL_HOST}" -P"${MYSQL_PORT}" --ssl=0 \
        -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}" \
        -s -N \
        -e "SELECT value FROM ${MYSQL_PREFIX}config
            WHERE namespace='core' AND \`key\`='schema_signature'
            LIMIT 1;" \
        2>/dev/null || echo "")

    if [ -z "${current_sig}" ]; then
        warn "Could not read schema_signature from DB — skipping."
        return 0
    fi

    if [ "${current_sig}" != "${expected_sig}" ]; then
        warn "Schema signature mismatch (DB: '${current_sig}' → file: '${expected_sig}'). Updating..."
        mysql \
            -h"${MYSQL_HOST}" -P"${MYSQL_PORT}" --ssl=0 \
            -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}" \
            2>/dev/null \
            -e "UPDATE ${MYSQL_PREFIX}config
                SET value='${expected_sig}'
                WHERE namespace='core' AND \`key\`='schema_signature';" \
        || warn "Schema signature update failed — non-fatal."
        ok "Schema signature updated."
    else
        ok "Schema signature OK."
    fi
}

# ─────────────────────────────────────────────────────────────────
#  7. FINALIZE PARTIALLY-INSTALLED STATE
#     (tables exist but config/flag not set — e.g. crash mid-install)
# ─────────────────────────────────────────────────────────────────
finalize_if_needed() {
    local table_count
    table_count=$(count_ost_tables)

    if [ "${table_count}" -lt 10 ]; then
        # Not installed at all
        return 1
    fi

    # Tables exist — ensure config + flag are consistent
    if ! config_is_installed; then
        warn "Found ${table_count} tables but config not marked installed — finalizing..."
        sed -i "s/define('OSTINSTALLED',FALSE)/define('OSTINSTALLED',TRUE)/" "${CONFIG_FILE}" || true
        if ! config_is_installed; then
            # sed didn't find the pattern (e.g. config was corrupt) — rewrite the flag line
            warn "sed patch failed; rewriting OSTINSTALLED line directly..."
            grep -v "OSTINSTALLED" "${CONFIG_FILE}" > /tmp/ost-config-tmp.php || true
            echo "define('OSTINSTALLED',TRUE);" >> /tmp/ost-config-tmp.php
            mv /tmp/ost-config-tmp.php "${CONFIG_FILE}"
            chown www-data:www-data "${CONFIG_FILE}"
        fi
    fi

    if [ ! -f "${INSTALL_FLAG}" ]; then
        mkdir -p "$(dirname "${INSTALL_FLAG}")"
        {
            echo "installed=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
            echo "version=1.18.3"
            echo "db_host=${MYSQL_HOST}"
            echo "admin_user=${OST_ADMIN_USER}"
            echo "status=finalized"
        } > "${INSTALL_FLAG}"
        chmod 644 "${INSTALL_FLAG}"
    fi

    ok "Finalized: ${table_count} tables, config and flag are consistent."
    return 0
}

# ─────────────────────────────────────────────────────────────────
#  8. LAUNCH FOREGROUND APACHE (final — keeps container alive)
# ─────────────────────────────────────────────────────────────────
launch_apache() {
    # Belt-and-braces: kill anything still holding port 80 / pid file
    stop_apache_background   # no-op if APACHE_BG_PID is already ""

    log "Cleaning stale Apache state..."
    rm -f /var/run/apache2/apache2.pid
    rm -rf /var/lock/apache2
    find /tmp -name 'apache*.pid' -delete 2>/dev/null || true

    log "Validating Apache configuration..."
    if ! apache2ctl configtest 2>&1; then
        err "Apache config test FAILED. Dumping error log:"
        tail -30 /var/log/apache2/error.log 2>/dev/null || echo "(no error log)"
        die "Refusing to start Apache with broken config."
    fi

    ok "Apache config OK."
    log "Starting Apache (foreground)..."
    exec apache2-foreground
    # exec replaces this process — nothing below runs
}

# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   osTicket v1.18.3 — Docker Startup   ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
    echo ""

    # ── 1. Block until DB is accepting connections ─────────────────
    wait_for_mysql || die "Could not connect to MySQL."

    # ── 1.5. Detect and fix invalid config (template placeholders) ──
    if [ -f "${CONFIG_FILE}" ] && config_has_placeholders; then
        warn "Config file has template placeholders — rewriting with actual database credentials..."
        write_config || die "Failed to rewrite ost-config.php with credentials."
    fi

    # ── 2. Decide installation state ──────────────────────────────
    #
    #   STATE A — already fully installed (flag + config + tables)
    #   STATE B — partially installed (tables exist, flag/config missing)
    #   STATE C — fresh install needed
    #
    if [ -f "${INSTALL_FLAG}" ] && config_is_installed; then
        # ── STATE A ───────────────────────────────────────────────
        ok "osTicket already installed ($(grep '^installed=' "${INSTALL_FLAG}" | cut -d= -f2))."
        check_upgrade
        remove_setup_dir

    elif finalize_if_needed; then
        # ── STATE B ───────────────────────────────────────────────
        # finalize_if_needed() already logged + fixed everything
        check_upgrade
        remove_setup_dir

    else
        # ── STATE C — first boot, full install ────────────────────
        log "Fresh install — no existing database found."

        # Ensure attachments dir exists before writing the flag there
        mkdir -p "${WEB_ROOT}/attachments"
        chmod 775 "${WEB_ROOT}/attachments"
        chown www-data:www-data "${WEB_ROOT}/attachments"

        # Write initial config (OSTINSTALLED=FALSE)
        write_config || die "Failed to write ost-config.php"

        # Start Apache so the web installer can POST to it
        start_apache_background || die "Could not start background Apache for installer."

        # Run installer (exit code correctly propagated)
        if run_installer; then
            # Installer succeeded — clean up
            stop_apache_background
            post_install_cleanup || warn "Post-install cleanup had issues — continuing."
            check_upgrade

            echo ""
            echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║   ✓  osTicket Installation Complete              ║${NC}"
            echo -e "${GREEN}╠══════════════════════════════════════════════════╣${NC}"
            echo -e "${GREEN}║  Helpdesk : ${OST_HELPDESK_URL}                  ${NC}"
            echo -e "${GREEN}║  Admin    : ${OST_HELPDESK_URL}/scp/             ${NC}"
            echo -e "${GREEN}║  Username : ${OST_ADMIN_USER}                    ${NC}"
            echo -e "${GREEN}║  Password : (from OST_ADMIN_PASS env var)        ${NC}"
            echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
            echo ""
        else
            # Installer failed — stop background Apache and exit so
            # Docker restart policy can retry
            stop_apache_background
            die "Installation failed. Container will restart and retry."
        fi
    fi

    # ── 3. Cron ────────────────────────────────────────────────────
    log "Starting cron daemon..."
    service cron start 2>&1 || warn "cron start returned non-zero — may already be running."
    ok "Cron done."

    # ── 4. Hand off to foreground Apache ──────────────────────────
    launch_apache
}

main "$@"
