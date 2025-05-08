import logging
import requests
import time
import datetime
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse

from app.core.config import settings
from app.scraper.html_parser import HTMLParser
from app.models.schema import ScrapeType

logger = logging.getLogger(__name__)

class WebScraper:
    """
    Web Scraper for extracting data from websites
    
    This class handles the HTTP requests and coordination of
    extraction using the HTMLParser
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        selector: Optional[str] = None,
        scrape_type: ScrapeType = ScrapeType.TEXT
    ):
        """
        Initialize the scraper with configuration
        
        Args:
            config: Dictionary of configuration options
            selector: CSS selector to target specific elements
            scrape_type: Type of data to scrape
        """
        self.config = config or {}
        self.selector = selector
        self.scrape_type = scrape_type
        
        # Set default values from config or settings
        self.user_agent = self.config.get('user_agent', settings.DEFAULT_USER_AGENT)
        self.timeout = self.config.get('timeout', settings.REQUEST_TIMEOUT)
        self.max_retries = self.config.get('max_retries', settings.MAX_RETRIES)
        self.retry_delay = self.config.get('retry_delay', settings.RETRY_DELAY)
        
        # Set up headers
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Update with any custom headers
        if 'headers' in self.config:
            self.headers.update(self.config['headers'])
    
    def _make_request(self, url: str) -> str:
        """
        Make an HTTP request to the specified URL with retries
        
        Args:
            url: The URL to request
            
        Returns:
            HTML content of the page
            
        Raises:
            Exception: If the request fails after all retries
        """
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL: {url}")
        
        # Set up request parameters
        params = {
            'url': url,
            'headers': self.headers,
            'timeout': self.timeout,
        }
        
        # Add optional parameters from config
        if 'cookies' in self.config:
            params['cookies'] = self.config['cookies']
        
        if 'proxies' in self.config:
            params['proxies'] = self.config['proxies']
            
        # Try making the request with retries
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making request to {url} (attempt {attempt+1}/{self.max_retries})")
                response = requests.get(**params)
                
                # Check if request was successful
                response.raise_for_status()
                
                # Log success and return content
                logger.info(f"Successfully retrieved content from {url}")
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{self.max_retries}): {str(e)}")
                
                # If this was the last attempt, raise the exception
                if attempt == self.max_retries - 1:
                    raise Exception(f"Failed to retrieve content after {self.max_retries} attempts: {str(e)}")
                
                # Otherwise, wait and retry
                time.sleep(self.retry_delay)
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape the specified URL and extract data
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary with the scraped data and metadata
        """
        # Get HTML content
        html_content = self._make_request(url)
        
        # Parse the HTML
        parser = HTMLParser(html_content, self.selector)
        
        # Extract data based on scrape type
        if self.scrape_type == ScrapeType.TEXT:
            data = parser.extract_text()
        elif self.scrape_type == ScrapeType.TABLES:
            data = parser.extract_tables()
        elif self.scrape_type == ScrapeType.LINKS:
            data = parser.extract_links()
        elif self.scrape_type == ScrapeType.IMAGES:
            data = parser.extract_images()
        elif self.scrape_type == ScrapeType.FULL:
            data = parser.extract_full()
        else:
            raise ValueError(f"Unsupported scrape type: {self.scrape_type}")
        
        # Return the result with metadata
        return {
            "url": url,
            "scrape_type": self.scrape_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": data
        }
