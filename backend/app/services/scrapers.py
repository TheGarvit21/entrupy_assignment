import asyncio
import random
import json
import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import os

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all marketplace scrapers"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.retry_count = 3
        self.retry_delay = 1 # seconds

    @abstractmethod
    async def fetch_product_data(self, external_id: str) -> Optional[Dict]:
        """Fetch product details from the marketplace"""
        pass

    async def fetch_with_retry(self, external_id: str) -> Optional[Dict]:
        """Fetch with retry logic"""
        for attempt in range(self.retry_count):
            try:
                # Simulate network delay
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
                # Simulate intermittent failure (10% chance)
                if random.random() < 0.1:
                    raise Exception(f"Simulated network error for {self.source_name} (Attempt {attempt+1})")
                
                return await self.fetch_product_data(external_id)
                
            except Exception as e:
                logger.warning(f"Error fetching from {self.source_name}: {str(e)}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt)) # Exponential backoff
                else:
                    logger.error(f"Failed to fetch from {self.source_name} after {self.retry_count} attempts")
                    return None

class MockScraper(BaseScraper):
    """Mock scraper that reads from static JSON file to simulate real scraping"""
    
    def __init__(self, source_name: str):
        super().__init__(source_name)
        self.data_file = os.path.join(os.path.dirname(__file__), "mock_data.json")

    async def fetch_product_data(self, external_id: str) -> Optional[Dict]:
        with open(self.data_file, "r") as f:
            data = json.load(f)
        
        products = data.get(self.source_name, [])
        product = next((p for p in products if p["external_id"] == external_id), None)
        
        if product:
            # Simulate real-time price fluctuations (80% chance of staying same, 20% chance of changing)
            # This is to show the price history feature
            if random.random() < 0.2:
                change_percent = random.uniform(-0.1, 0.1) # Up to 10% change
                product["current_price"] = round(product["current_price"] * (1 + change_percent), 2)
            
            return product
        return None

class GrailedScraper(MockScraper):
    def __init__(self):
        super().__init__("grailed")

class FashionphileScraper(MockScraper):
    def __init__(self):
        super().__init__("fashionphile")

class OneStDibsScraper(MockScraper):
    def __init__(self):
        super().__init__("1stdibs")

class ScraperManager:
    """Manages multi-marketplace scrapers"""
    
    def __init__(self):
        self.scrapers = {
            "grailed": GrailedScraper(),
            "fashionphile": FashionphileScraper(),
            "1stdibs": OneStDibsScraper()
        }

    async def refresh_product(self, source: str, external_id: str) -> Optional[Dict]:
        scraper = self.scrapers.get(source.lower())
        if not scraper:
            logger.error(f"No scraper found for source: {source}")
            return None
        
        return await scraper.fetch_with_retry(external_id)
