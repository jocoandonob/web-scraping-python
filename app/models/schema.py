from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, model_validator

class ScrapeType(str, Enum):
    """Type of data to scrape"""
    TEXT = "text"
    TABLES = "tables"
    LINKS = "links"
    IMAGES = "images"
    FULL = "full"

class ScraperConfig(BaseModel):
    """Configuration options for the scraper"""
    follow_links: bool = Field(False, description="Whether to follow links on the page")
    max_depth: int = Field(1, description="Maximum depth for following links")
    timeout: int = Field(30, description="Request timeout in seconds")
    user_agent: Optional[str] = Field(None, description="Custom user agent string")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    cookies: Optional[Dict[str, str]] = Field(None, description="Custom cookies")
    proxies: Optional[Dict[str, str]] = Field(None, description="Proxy configuration")

class ScraperRequest(BaseModel):
    """Request model for the scraper endpoint"""
    url: HttpUrl = Field(..., description="The URL to scrape")
    scrape_type: ScrapeType = Field(ScrapeType.TEXT, description="Type of data to scrape")
    selector: Optional[str] = Field(None, description="CSS selector to target specific elements")
    config: Optional[ScraperConfig] = Field(None, description="Scraper configuration")

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://example.com",
                "scrape_type": "text",
                "selector": "div.content",
                "config": {
                    "follow_links": False,
                    "max_depth": 1,
                    "timeout": 30,
                    "user_agent": "Custom User Agent"
                }
            }
        }
    }

class ScrapeResult(BaseModel):
    """Result of a scraping operation"""
    url: HttpUrl
    data: Any
    scrape_type: ScrapeType
    timestamp: str

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: Optional[str] = None

class ScraperResponse(BaseResponse):
    """Response model for the scraper endpoint"""
    url: HttpUrl
    data: Any

class ScraperConfigResponse(BaseResponse):
    """Response model for the config endpoint"""
    config: Dict[str, Any]

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error: str
    status_code: int
