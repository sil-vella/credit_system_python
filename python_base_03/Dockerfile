# Base Image
FROM python:3.11-slim

# Install system dependencies, Vault CLI, MongoDB CLI, and Redis CLI
RUN apt-get update && apt-get install -y \
    nano \
    curl \
    gpg \
    lsb-release \
    gnupg \
    && curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list \
    && curl -fsSL https://pgp.mongodb.com/server-6.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-6.0.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg] http://repo.mongodb.org/apt/debian $(lsb_release -cs)/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list \
    && apt-get update \
    && apt-get install -y vault mongodb-mongosh mongodb-database-tools redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && vault --version \
    && mongosh --version \
    && redis-cli --version

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 5000

# Command to start the application
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:5000 app:app"]
