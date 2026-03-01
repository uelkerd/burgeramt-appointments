FROM python:3.10-slim

# Set a shared location for Playwright browsers so they can be found by any user
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

COPY . /var/appointments
WORKDIR /var/appointments

# Combine RUN commands to reduce layers. Install dependencies and browser as root.
RUN pip install --no-cache-dir . && \
    playwright install chromium --with-deps

# Create a non-root user to run the application for better security, and fix permissions
RUN useradd -m appuser && chown -R appuser:appuser /var/appointments /opt/pw-browsers

USER appuser

CMD ["appointments", "-q"]
