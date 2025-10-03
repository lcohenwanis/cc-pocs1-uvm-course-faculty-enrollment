"""
Web scraper for UVM course enrollment data.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from typing import List, Dict, Optional
import logging
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnrollmentScraper:
    """Scrapes UVM course enrollment data from the web."""
    
    def __init__(self, base_url: str = None):
        """Initialize the scraper."""
        self.base_url = base_url or config.BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_page(self, url: str) -> Optional[str]:
        """Fetch a page and return its content."""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            time.sleep(config.DELAY_BETWEEN_REQUESTS)
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
            
    def get_enrollment_links(self) -> List[Dict[str, str]]:
        """
        Parse the main enrollment page to get links to individual enrollment files.
        Returns a list of dicts with 'url', 'term', 'year' keys.
        """
        html = self.get_page(self.base_url)
        if not html:
            logger.error("Failed to fetch main enrollment page")
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Find all links that point to enrollment data files
        # The actual structure will depend on the website
        # This is a generic pattern that should be adjusted based on the actual HTML
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Look for patterns like "Fall2023.txt" or "spring2024.html"
            # Adjust the pattern based on actual website structure
            pattern = r'(fall|spring|summer|winter)[-_]?(\d{4})'
            match = re.search(pattern, href, re.IGNORECASE)
            
            if match:
                term = match.group(1).capitalize()
                year = int(match.group(2))
                
                # Filter by year range
                if config.START_YEAR <= year <= config.END_YEAR:
                    full_url = href if href.startswith('http') else f"{self.base_url.rsplit('/', 1)[0]}/{href}"
                    links.append({
                        'url': full_url,
                        'term': term,
                        'year': year,
                        'filename': href
                    })
                    
        logger.info(f"Found {len(links)} enrollment data files")
        return sorted(links, key=lambda x: (x['year'], x['term']))
        
    def parse_enrollment_data(self, html: str, term: str, year: int) -> List[Dict]:
        """
        Parse enrollment data from an HTML page.
        Returns a list of course records.
        """
        soup = BeautifulSoup(html, 'html.parser')
        courses = []
        
        # The actual parsing logic depends on the structure of the enrollment pages
        # This is a generic approach that should be adapted to the actual format
        
        # Look for tables or structured data
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # Skip header row
                cols = row.find_all(['td', 'th'])
                
                if len(cols) < 4:  # Need at least dept, course, title, instructor
                    continue
                    
                try:
                    # Extract course information
                    # Adjust indices based on actual table structure
                    course_info = {
                        'term': term,
                        'year': year,
                        'department': cols[0].get_text(strip=True),
                        'course_number': cols[1].get_text(strip=True),
                        'section': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                        'title': cols[3].get_text(strip=True) if len(cols) > 3 else '',
                        'instructor': cols[4].get_text(strip=True) if len(cols) > 4 else '',
                        'enrollment': self._parse_int(cols[5].get_text(strip=True)) if len(cols) > 5 else None,
                        'capacity': self._parse_int(cols[6].get_text(strip=True)) if len(cols) > 6 else None,
                        'crn': cols[7].get_text(strip=True) if len(cols) > 7 else None,
                    }
                    
                    if course_info['department'] and course_info['course_number']:
                        courses.append(course_info)
                        
                except (IndexError, AttributeError) as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
                    
        # Also try parsing tab-delimited format
        if not courses:
            courses = self._parse_tab_delimited(html, term, year)
            
        logger.info(f"Parsed {len(courses)} courses for {term} {year}")
        return courses
        
    def _parse_tab_delimited(self, content: str, term: str, year: int) -> List[Dict]:
        """Parse tab-delimited enrollment data."""
        courses = []
        lines = content.strip().split('\n')
        
        if not lines:
            return courses
            
        # Try to identify header row
        header_idx = 0
        for i, line in enumerate(lines[:5]):
            if 'dept' in line.lower() or 'course' in line.lower():
                header_idx = i
                break
                
        headers = lines[header_idx].split('\t')
        headers = [h.strip().lower() for h in headers]
        
        for line in lines[header_idx + 1:]:
            if not line.strip():
                continue
                
            fields = line.split('\t')
            if len(fields) < 3:
                continue
                
            course_info = {'term': term, 'year': year}
            
            # Map fields to our schema
            for i, field in enumerate(fields):
                field = field.strip()
                if i < len(headers):
                    header = headers[i]
                    
                    if 'dept' in header or 'subj' in header:
                        course_info['department'] = field
                    elif 'course' in header and 'title' not in header:
                        course_info['course_number'] = field
                    elif 'sect' in header:
                        course_info['section'] = field
                    elif 'title' in header or 'name' in header:
                        course_info['title'] = field
                    elif 'instr' in header or 'faculty' in header or 'teacher' in header:
                        course_info['instructor'] = field
                    elif 'enr' in header or 'enrolled' in header:
                        course_info['enrollment'] = self._parse_int(field)
                    elif 'cap' in header or 'max' in header:
                        course_info['capacity'] = self._parse_int(field)
                    elif 'crn' in header:
                        course_info['crn'] = field
                        
            if 'department' in course_info and 'course_number' in course_info:
                courses.append(course_info)
                
        return courses
        
    def _parse_int(self, value: str) -> Optional[int]:
        """Safely parse an integer from a string."""
        try:
            return int(re.sub(r'[^\d]', '', value))
        except (ValueError, TypeError):
            return None
            
    def scrape_all(self) -> List[Dict]:
        """
        Scrape all enrollment data within the configured year range.
        Returns a list of all course records.
        """
        all_courses = []
        links = self.get_enrollment_links()
        
        if not links:
            logger.warning("No enrollment links found. The site structure may have changed.")
            return all_courses
            
        for link_info in links:
            html = self.get_page(link_info['url'])
            if html:
                courses = self.parse_enrollment_data(
                    html, 
                    link_info['term'], 
                    link_info['year']
                )
                all_courses.extend(courses)
                logger.info(f"Total courses scraped: {len(all_courses)}")
                
        return all_courses
