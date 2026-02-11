FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for SQLite
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your project files (app.py, templates, static, expenses.db)
COPY . .

# Expose the port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
