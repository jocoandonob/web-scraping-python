import logging
from typing import List, Dict, Any, Optional, Union
from bs4 import BeautifulSoup, Tag
import pandas as pd
import trafilatura

logger = logging.getLogger(__name__)

class HTMLParser:
    """
    HTML Parser for extracting structured data from web pages
    using BeautifulSoup and other specialized libraries
    """
    
    def __init__(self, html_content: str, selector: Optional[str] = None):
        """
        Initialize the parser with HTML content
        
        Args:
            html_content: The HTML content to parse
            selector: Optional CSS selector to target specific elements
        """
        self.html = html_content
        self.selector = selector
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
    def _get_target_elements(self) -> List[Tag]:
        """Get the target elements based on selector"""
        if not self.selector:
            return [self.soup]
        
        try:
            elements = self.soup.select(self.selector)
            if not elements:
                logger.warning(f"No elements found for selector: {self.selector}")
            return elements
        except Exception as e:
            logger.error(f"Error selecting elements with {self.selector}: {str(e)}")
            return [self.soup]
    
    def extract_text(self) -> Union[str, List[str]]:
        """
        Extract text content from the HTML
        
        Returns:
            Either a single string or list of strings with the extracted text
        """
        # Try using trafilatura for main text extraction first if no specific selector
        if not self.selector:
            try:
                extracted = trafilatura.extract(self.html)
                if extracted:
                    return extracted
            except Exception as e:
                logger.warning(f"Trafilatura extraction failed, falling back to BeautifulSoup: {str(e)}")
        
        # Fall back to BeautifulSoup
        elements = self._get_target_elements()
        
        if len(elements) == 1:
            return elements[0].get_text(strip=True, separator=' ')
        
        return [el.get_text(strip=True, separator=' ') for el in elements]
    
    def extract_tables(self) -> List[Dict[str, Any]]:
        """
        Extract tables from the HTML
        
        Returns:
            List of tables as dictionaries
        """
        tables = []
        elements = self._get_target_elements()
        
        for element in elements:
            # Find all tables within the element
            html_tables = element.find_all('table')
            
            if not html_tables:
                logger.info("No tables found in the HTML")
                continue
            
            for i, table in enumerate(html_tables):
                try:
                    # Use pandas to extract the table
                    df = pd.read_html(str(table))[0]
                    tables.append({
                        "table_index": i,
                        "headers": df.columns.tolist(),
                        "data": df.to_dict(orient='records')
                    })
                except Exception as e:
                    logger.error(f"Error parsing table {i}: {str(e)}")
        
        return tables
    
    def extract_links(self) -> List[Dict[str, str]]:
        """
        Extract links from the HTML
        
        Returns:
            List of dictionaries with link information
        """
        elements = self._get_target_elements()
        links = []
        
        for element in elements:
            for a_tag in element.find_all('a', href=True):
                try:
                    links.append({
                        "url": a_tag['href'],
                        "text": a_tag.get_text(strip=True) or "",
                        "title": a_tag.get('title', ""),
                    })
                except Exception as e:
                    logger.error(f"Error extracting link: {str(e)}")
        
        return links
    
    def extract_images(self) -> List[Dict[str, str]]:
        """
        Extract image information from the HTML
        
        Returns:
            List of dictionaries with image information
        """
        elements = self._get_target_elements()
        images = []
        
        for element in elements:
            for img_tag in element.find_all('img', src=True):
                try:
                    images.append({
                        "src": img_tag['src'],
                        "alt": img_tag.get('alt', ""),
                        "title": img_tag.get('title', ""),
                        "width": img_tag.get('width', ""),
                        "height": img_tag.get('height', ""),
                    })
                except Exception as e:
                    logger.error(f"Error extracting image: {str(e)}")
        
        return images
    
    def extract_full(self) -> Dict[str, Any]:
        """
        Extract all types of data from the HTML
        
        Returns:
            Dictionary with all extracted data
        """
        return {
            "text": self.extract_text(),
            "tables": self.extract_tables(),
            "links": self.extract_links(),
            "images": self.extract_images(),
        }
