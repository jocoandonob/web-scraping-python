from flask import Flask, render_template, request, jsonify
import trafilatura
import requests
import json
import logging
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Request history for rate limiting
request_history = {}
RATE_LIMIT = 10  # Requests per minute

def get_website_text_content(url):
    """
    This function takes a URL and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return "Failed to fetch content from the URL"
        
        text = trafilatura.extract(downloaded)
        return text or "No content extracted"
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        return f"Error: {str(e)}"

def extract_tables(html_content):
    """Extract tables from HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = []
        
        html_tables = soup.find_all('table')
        for i, table in enumerate(html_tables):
            rows = []
            for tr in table.find_all('tr'):
                cells = []
                for cell in tr.find_all(['td', 'th']):
                    cells.append(cell.get_text(strip=True))
                if cells:
                    rows.append(cells)
            
            if rows:
                tables.append({
                    "table_index": i,
                    "rows": rows
                })
        
        return tables
    except Exception as e:
        logger.error(f"Error extracting tables: {str(e)}")
        return []

def extract_links(html_content):
    """Extract links from HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            links.append({
                "url": a_tag['href'],
                "text": a_tag.get_text(strip=True) or "",
                "title": a_tag.get('title', ""),
            })
        
        return links
    except Exception as e:
        logger.error(f"Error extracting links: {str(e)}")
        return []

def extract_images(html_content):
    """Extract images from HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        images = []
        
        for img_tag in soup.find_all('img', src=True):
            images.append({
                "src": img_tag['src'],
                "alt": img_tag.get('alt', ""),
                "title": img_tag.get('title', ""),
                "width": img_tag.get('width', ""),
                "height": img_tag.get('height', ""),
            })
        
        return images
    except Exception as e:
        logger.error(f"Error extracting images: {str(e)}")
        return []

def validate_url(url):
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except:
        return False

def rate_limiter(client_ip):
    """Apply rate limiting"""
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(minutes=1)
    
    # Clean old requests
    for ip, timestamps in list(request_history.items()):
        request_history[ip] = [ts for ts in timestamps if ts > cutoff]
        if not request_history[ip]:
            del request_history[ip]
    
    # Check if rate limit exceeded
    if client_ip not in request_history:
        request_history[client_ip] = []
    
    if len(request_history[client_ip]) >= RATE_LIMIT:
        return False
    
    # Add current request
    request_history[client_ip].append(now)
    return True

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape_url():
    client_ip = request.remote_addr
    
    # Apply rate limiting
    if not rate_limiter(client_ip):
        return jsonify({
            "success": False,
            "message": "Rate limit exceeded. Please try again later."
        }), 429
    
    try:
        data = request.get_json()
        url = data.get('url')
        scrape_type = data.get('scrape_type', 'text')
        selector = data.get('selector')
        
        # Validate URL
        if not url or not validate_url(url):
            return jsonify({
                "success": False,
                "message": "Invalid URL provided"
            }), 400
        
        # Get HTML content
        user_agent = data.get('config', {}).get('user_agent', 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        timeout = data.get('config', {}).get('timeout', 30)
        
        response = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
        html_content = response.text
        
        # Extract based on scrape type
        result = {}
        
        if scrape_type == 'text':
            result = get_website_text_content(url)
        elif scrape_type == 'tables':
            result = extract_tables(html_content)
        elif scrape_type == 'links':
            result = extract_links(html_content)
        elif scrape_type == 'images':
            result = extract_images(html_content)
        elif scrape_type == 'full':
            result = {
                "text": get_website_text_content(url),
                "tables": extract_tables(html_content),
                "links": extract_links(html_content),
                "images": extract_images(html_content),
            }
        
        # Create response with metadata
        return jsonify({
            "success": True,
            "url": url,
            "data": {
                "scrape_type": scrape_type,
                "timestamp": datetime.datetime.now().isoformat(),
                "data": result
            },
            "message": "Scraping completed successfully"
        })
        
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to scrape URL: {str(e)}"
        }), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get the current scraper configuration options"""
    remaining = RATE_LIMIT
    if request.remote_addr in request_history:
        remaining = max(0, RATE_LIMIT - len(request_history[request.remote_addr]))
    
    config = {
        "available_scrape_types": ["text", "tables", "links", "images", "full"],
        "rate_limit": {
            "requests_per_minute": RATE_LIMIT,
            "remaining": remaining
        },
        "supported_output_formats": ["json", "csv"],
        "default_config": {
            "timeout": 30,
            "user_agent": "WebScraper Bot 1.0"
        }
    }
    
    return jsonify({
        "success": True,
        "config": config
    })

@app.route('/api/rate-limit', methods=['GET'])
def check_rate_limit():
    """Check current rate limit status"""
    client_ip = request.remote_addr
    remaining = RATE_LIMIT
    
    if client_ip in request_history:
        # Clean old requests
        now = datetime.datetime.now()
        cutoff = now - datetime.timedelta(minutes=1)
        request_history[client_ip] = [ts for ts in request_history[client_ip] if ts > cutoff]
        
        remaining = max(0, RATE_LIMIT - len(request_history[client_ip]))
    
    return jsonify({"remaining_requests": remaining})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)