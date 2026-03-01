FROM python:3.10-slim

# Set a shared location for Playwright browsers so they can be found by any user
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

WORKDIR /var/appointments

# Copy only dependency metadata first to leverage Docker layer caching.
# We use wildcards so it works whether setup.py or pyproject.toml exists.
COPY setup.p[y] pyproject.tom[l] README.md ./
# Also copy the appointments module structure since setup.py's find_packages() needs it
COPY appointments/ ./appointments/

# Combine RUN commands to reduce layers. Install dependencies and browser as root.
RUN pip install --no-cache-dir . && \
    playwright install chromium --with-deps

# Copy the rest of the source code
COPY . .

# Create a non-root user to run the application for better security, and fix permissions
RUN useradd -m appuser && chown -R appuser:appuser /var/appointments /opt/pw-browsers

USER appuser

CMD ["appointments", "-q"]

