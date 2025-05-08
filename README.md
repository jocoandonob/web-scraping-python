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

## Docker Instructions

### Building the Docker Image

To build the Docker image, run the following command in the root directory of the project:

```bash
docker build -t your-image-name .
```

### Pushing the Docker Image

1. **Tag the image with your registry URL:**

   ```bash
   docker tag your-image-name your-registry-url/your-image-name:tag
   ```

   Replace `your-registry-url` with your Docker registry URL (e.g., `docker.io/yourusername`), `your-image-name` with the name you used when building the image, and `tag` with the version or tag you want to use.

2. **Push the image to the registry:**

   ```bash
   docker push your-registry-url/your-image-name:tag
   ```

   Make sure you are logged in to your Docker registry. You can log in using:

   ```bash
   docker login your-registry-url
   ```

   Enter your username and password when prompted.

### Running the Docker Container

To run the Docker container, use the following command:

```bash
docker run -p 5000:5000 your-image-name
```

This will map port 5000 of the container to port 5000 on your host machine. 