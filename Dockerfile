# Use a specific slim Debian base image for better reproducibility
FROM python:3.10.13-slim-bookworm

# Explicitly define where Playwright should store its binaries
# This ensures it can be accessed by any user in the container
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

WORKDIR /app

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
RUN useradd -m appuser && chown -R appuser:appuser /app /opt/pw-browsers

USER appuser

CMD ["appointments", "-q"]

