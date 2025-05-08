import csv
import io
import logging
import json
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends, Form, Response, status, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import HttpUrl, ValidationError

from app.models.schema import (
    ScraperRequest, 
    ScraperResponse, 
    ScraperConfigResponse,
    ScrapeResult,
    ErrorResponse
)
from app.scraper.scraper import WebScraper
from app.utils.rate_limiter import rate_limiter, get_remaining_requests
from app.utils.validators import validate_url

api_router = APIRouter()
logger = logging.getLogger(__name__)

@api_router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}

@api_router.post("/scrape", response_model=ScraperResponse)
async def scrape_url(
    request: ScraperRequest,
    background_tasks: BackgroundTasks,
    dependency=Depends(rate_limiter)
):
    """
    Scrape a URL and return structured data
    
    This endpoint extracts data from the specified URL using the configured scraper.
    Rate limiting is applied to prevent overloading target websites.
    """
    try:
        # Validate URL
        validate_url(request.url)
        
        # Create scraper instance with config
        scraper = WebScraper(
            config=request.config if request.config else {},
            selector=request.selector,
            scrape_type=request.scrape_type
        )
        
        # Execute scraping
        result = scraper.scrape(request.url)
        
        # Add rate limit info to response headers
        response = ScraperResponse(
            success=True,
            url=request.url,
            data=result,
            message="Scraping completed successfully"
        )
        
        # Log the successful scraping
        background_tasks.add_task(
            logger.info,
            f"Successfully scraped {request.url}"
        )
        
        return response
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape URL: {str(e)}"
        )

@api_router.get("/config", response_model=ScraperConfigResponse)
async def get_scraper_config():
    """Get the current scraper configuration options"""
    config = {
        "available_scrape_types": ["text", "tables", "links", "images", "full"],
        "rate_limit": {
            "requests_per_minute": 10,
            "remaining": get_remaining_requests()
        },
        "supported_output_formats": ["json", "csv"],
        "default_config": {
            "follow_links": False,
            "max_depth": 1,
            "timeout": 30,
            "user_agent": "WebScraper Bot 1.0"
        }
    }
    return ScraperConfigResponse(success=True, config=config)

@api_router.post("/export/{format}")
async def export_scrape_data(
    format: str,
    result: ScrapeResult,
    dependency=Depends(rate_limiter)
):
    """
    Export scraped data in various formats
    
    Args:
        format: The output format (json or csv)
        result: The scrape result to export
    """
    if format.lower() not in ["json", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format. Use 'json' or 'csv'."
        )
        
    try:
        if format.lower() == "json":
            # Return data as JSON
            return result
            
        elif format.lower() == "csv":
            # Process data to CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Handle different data structures
            if isinstance(result.data, list):
                # If data is a list of dictionaries with uniform keys
                if result.data and isinstance(result.data[0], dict):
                    # Write headers
                    headers = result.data[0].keys()
                    writer.writerow(headers)
                    
                    # Write data rows
                    for item in result.data:
                        writer.writerow([item.get(key, "") for key in headers])
                else:
                    # Simple list - just write one column
                    writer.writerow(["value"])
                    for item in result.data:
                        writer.writerow([item])
            elif isinstance(result.data, dict):
                # Dictionary - keys as headers, values as row
                writer.writerow(result.data.keys())
                writer.writerow(result.data.values())
            
            # Prepare response
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=scraped_data.csv"
                }
            )
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )

@api_router.get("/rate-limit")
async def check_rate_limit():
    """Check current rate limit status"""
    remaining = get_remaining_requests()
    return {"remaining_requests": remaining}
