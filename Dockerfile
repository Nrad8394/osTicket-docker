# ─────────────────────────────────────────────────────────────────
#  osTicket v1.18.3 — Fully Automated Docker Image
#  PHP 8.2 + Apache  |  Zero-touch install on first boot
# ─────────────────────────────────────────────────────────────────
FROM php:8.2-apache

ARG OSTICKET_DIR=./osTicket-v1.18.3/upload

# ── System packages & PHP extensions ─────────────────────────────
# NOTE: php:8.2-apache uses Debian Bookworm base with updated packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpng-dev \
        libjpeg62-turbo-dev \
        libfreetype6-dev \
        libzip-dev \
        libxml2-dev \
        libonig-dev \
        libldap2-dev \
        libkrb5-dev \
        libicu-dev \
        default-mysql-client \
        cron \
        curl \
        unzip \
        netcat-openbsd \
    && docker-php-ext-configure gd \
        --with-freetype \
        --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
        gd \
        mysqli \
        pdo \
        pdo_mysql \
        zip \
        xml \
        mbstring \
        intl \
        ldap \
        opcache \
    && pecl install apcu \
    && docker-php-ext-enable apcu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Apache configuration ──────────────────────────────────────────
RUN a2enmod rewrite headers expires deflate

COPY config/apache-osticket.conf /etc/apache2/sites-available/osticket.conf
RUN a2dissite 000-default.conf && a2ensite osticket.conf

# ── PHP configuration ─────────────────────────────────────────────
COPY config/php-osticket.ini /usr/local/etc/php/conf.d/99-osticket.ini

# ── osTicket source files ─────────────────────────────────────────
WORKDIR /var/www/html

COPY ${OSTICKET_DIR}/ ./

# ── Fix installer paths: copy setup streams to upgrader location ──
RUN mkdir -p /var/www/html/include/upgrader/streams/core && \
    cp -r /var/www/html/setup/inc/streams/core/* /var/www/html/include/upgrader/streams/core/ && \
    md5sum /var/www/html/include/upgrader/streams/core/install-mysql.sql | awk '{print $1}' > /var/www/html/include/upgrader/streams/core.sig

# ── Config file — writable for installer, then locked after setup ─
RUN cp /var/www/html/include/ost-sampleconfig.php \
       /var/www/html/include/ost-config.php \
    && chmod 0666 /var/www/html/include/ost-config.php

# ── Create attachments directory ──────────────────────────────────
RUN mkdir -p /var/www/html/attachments

# ── Ownership & permissions ───────────────────────────────────────
RUN chown -R www-data:www-data /var/www/html \
    && find /var/www/html -type d -exec chmod 755 {} \; \
    && find /var/www/html -type f -exec chmod 644 {} \; \
    && chmod 0666 /var/www/html/include/ost-config.php \
    && chmod 775  /var/www/html/attachments

# ── Cron job (runs osTicket task scheduler every 5 min) ──────────
RUN echo "*/5 * * * * www-data /usr/local/bin/php /var/www/html/api/cron.php > /dev/null 2>&1" \
        > /etc/cron.d/osticket \
    && chmod 0644 /etc/cron.d/osticket

# ── Entrypoint ────────────────────────────────────────────────────
COPY scripts/entrypoint.sh /entrypoint.sh
COPY scripts/web-install.sh /usr/local/bin/web-install.sh
RUN  chmod +x /entrypoint.sh \
    && chmod +x /usr/local/bin/web-install.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]