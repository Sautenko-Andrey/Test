FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y wget gnupg2 ca-certificates \
       libgtk-3-0 libxss1 libgconf-2-4 libnss3 libasound2 \
       libatk1.0-0 libatk-bridge2.0-0 libx11-xcb1 libgbm1 \
       xvfb curl unzip && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["python", "app/main.py"]
