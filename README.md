# Flask Web Scraper

This project is a Flask-based web application for scraping website content, including text, tables, links, and images. It provides a REST API and a simple web interface.

## Features

- Extracts main text content from web pages
- Extracts tables, links, and images from HTML
- Rate limiting to prevent abuse
- Configurable user agent and timeout
- REST API endpoints for scraping and configuration

## Requirements

- Python 3.11+
- See `pyproject.toml` for all dependencies

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-directory>
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or, if using `pyproject.toml`:
   ```bash
   pip install .
   ```

## Running the App

### Development Server

```bash
python app.py
```

or

```bash
flask run
```

### Production (with Gunicorn)

```bash
gunicorn app:application
```

## API Endpoints

- `POST /api/scrape` — Scrape a URL (text, tables, links, images, or all)
- `GET /api/config` — Get current configuration
- `GET /api/rate-limit` — Check rate limit status

## Project Structure

- `app.py` — WSGI entry point
- `flask_app.py` — Main Flask app and routes
- `templates/` — HTML templates
- `static/` — Static files (CSS, JS, images)

## License

MIT (or specify your license) 