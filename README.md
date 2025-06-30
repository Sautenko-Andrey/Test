# AutoRia Scraper

Application for daily asynchronous scraping of used car listings from the AutoRia platform and saving them to PostgreSQL.


## 1. Project Structure

autoriascraper/
├─ app/
├─ dumps/             
├─ .env          
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
└─ README.md


## 2. Prerequisites

- Docker & Docker Compose  
- Git  
- Python 3.10+ 


## 3. Configuration (`.env`)

3.1 Create `.env` file in project root with:

START_URL=https://auto.ria.com/uk/car/used/
DB_HOST=db
DB_PORT=5432
DB_NAME=autoriascraper
DB_USER=postgres
DB_PASSWORD=ВашСекретныйПароль
SCRAPE_TIME=12:00
DUMP_TIME=12:00
MAX_CONCURRENT_REQUESTS=10


## 4. Docker Setup

4.1 Clone repository:
    git clone https://github.com/Sautenko-Andrey/Test

4.2 Navigate to project directory:
    cd autoriascraper

4.3 Create and configure `.env` (see section 3)

4.4 Build and launch services:
    docker-compose up --build

4.5 Verify running containers:
    docker ps

## 5. Local Setup (without Docker)

5.1 Create and activate virtual environment:
    python3 -m venv .venv
    source .venv/bin/activate

5.2 Install dependencies:
    pip install -r requirements.txt

5.3 Start a local PostgreSQL and configure `.env`

5.4 Launch application:
    python app/main.py


## 6. Next Steps

