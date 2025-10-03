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
        Returns a list of dicts with 'url', 'term', 'year', 'csv_url' keys.
        """
        html = self.get_page(self.base_url)
        if not html:
            logger.error("Failed to fetch main enrollment page")
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        base_url = self.base_url.rsplit('/', 1)[0]  # Remove filename to get base URL
        
        # Find all links that point to enrollment data files
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Look for links to curr_enroll_*.html files
            # Pattern: curr_enroll_YYYYMM.html where MM is 01=Spring, 06=Summer, 09=Fall
            pattern = r'curr_enroll_(\d{4})(\d{2})\.html'
            match = re.search(pattern, href)
            
            if match:
                year = int(match.group(1))
                month_code = match.group(2)
                
                # Map month codes to terms
                term_map = {'01': 'Spring', '06': 'Summer', '09': 'Fall'}
                term = term_map.get(month_code, f'Unknown{month_code}')
                
                # Filter by year range
                if config.START_YEAR <= year <= config.END_YEAR:
                    # Build URLs for the HTML page and the CSV data
                    html_url = f"{base_url}/{href}" if not href.startswith('http') else href
                    csv_filename = href.replace('.html', '.txt')  # CSV data is in .txt format
                    csv_url = f"{base_url}/{csv_filename}"
                    
                    links.append({
                        'url': html_url,
                        'csv_url': csv_url,
                        'term': term,
                        'year': year,
                        'filename': href,
                        'term_code': f"{year}{month_code}"
                    })
                    
        logger.info(f"Found {len(links)} enrollment data files")
        return sorted(links, key=lambda x: (x['year'], x['term']))
        
    def get_csv_data(self, csv_url: str) -> Optional[str]:
        """
        Download CSV data from the given URL.
        Returns the CSV content as a string, or None if failed.
        """
        try:
            logger.info(f"Downloading CSV data from: {csv_url}")
            response = self.session.get(csv_url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            time.sleep(config.DELAY_BETWEEN_REQUESTS)
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error downloading CSV from {csv_url}: {e}")
            return None
        
    def parse_enrollment_data(self, csv_content: str, term: str, year: int) -> List[Dict]:
        """
        Parse enrollment data from CSV content.
        Handles multiple format versions automatically.
        Returns a list of course records.
        """
        courses = []
        
        if not csv_content:
            logger.warning(f"No CSV content to parse for {term} {year}")
            return courses
            
        # Split into lines and clean up
        lines = [line.strip() for line in csv_content.split('\n') if line.strip()]
        
        if len(lines) < 2:
            logger.warning(f"Not enough data lines for {term} {year}")
            return courses
            
        # Parse header to understand column positions
        import csv
        from io import StringIO
        
        try:
            # Use CSV reader to properly handle quoted values
            csv_reader = csv.reader(StringIO(csv_content))
            header = next(csv_reader)
            
            # Clean header names and create mapping
            header = [col.strip() for col in header]
            
            # Detect format based on header structure
            format_version = self._detect_format_version(header)
            logger.info(f"Detected format version: {format_version}")
            
            # Map columns based on detected format
            col_mapping = self._map_columns_by_format(header, format_version)
            logger.info(f"Mapped columns: {col_mapping}")
            
            # Parse data rows
            for row in csv_reader:
                if len(row) < max(col_mapping.values(), default=[0]) + 1:
                    continue  # Skip incomplete rows
                    
                try:
                    # Extract basic course information - use safe column access
                    course_info = {
                        'term': term,
                        'year': year,
                        'department': self._safe_get_field(row, col_mapping, 'department'),
                        'course_number': self._safe_get_field(row, col_mapping, 'course_number'),
                        'section': self._safe_get_field(row, col_mapping, 'section'),
                        'title': self._safe_get_field(row, col_mapping, 'title'),
                        'crn': self._safe_get_field(row, col_mapping, 'crn'),
                        'instructor': self._safe_get_field(row, col_mapping, 'instructor'),
                        'netid': self._safe_get_field(row, col_mapping, 'netid'),
                        'email': self._safe_get_field(row, col_mapping, 'email'),
                    }
                    
                    # Parse numeric fields
                    if 'enrollment' in col_mapping:
                        course_info['enrollment'] = self._parse_int(self._safe_get_field(row, col_mapping, 'enrollment'))
                    if 'capacity' in col_mapping:
                        course_info['capacity'] = self._parse_int(self._safe_get_field(row, col_mapping, 'capacity'))
                    
                    # Add additional fields if available (varies by format)
                    optional_fields = ['credits', 'days', 'start_time', 'end_time', 'building', 'room', 
                                     'ptrm', 'lec_lab', 'attr', 'camp_code', 'coll_code', 'true_max',
                                     'gp_ind', 'fees', 'xlistings']
                    for field in optional_fields:
                        if field in col_mapping:
                            course_info[field] = self._safe_get_field(row, col_mapping, field)
                    
                    # Only include rows with valid department and course number
                    if course_info['department'] and course_info['course_number']:
                        courses.append(course_info)
                        
                except (IndexError, ValueError) as e:
                    logger.debug(f"Error parsing CSV row: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing CSV data for {term} {year}: {e}")
            return []
            
        logger.info(f"Parsed {len(courses)} courses for {term} {year}")
        return courses
    
    def _detect_format_version(self, header: list) -> str:
        """
        Detect the format version based on header columns.
        Returns: 'old' (2012 and earlier), 'middle' (2013-2024), or 'new' (2025+)
        """
        header_lower = [col.lower().strip() for col in header]
        
        # Check for newer format indicators (25 columns with specific fields)
        if 'ptrm' in header_lower and 'coll code' in header_lower and len(header) >= 24:
            return 'new'  # 2025+ format
        
        # Check for middle format indicators (NetId/Email but not all new fields)
        elif 'netid' in header_lower or 'email' in header_lower:
            return 'middle'  # 2013-2024 format
        
        # Check for old format indicators (Dept instead of Subj, no NetId/Email)
        elif any('dept' in col.lower() for col in header_lower) and 'netid' not in header_lower:
            return 'old'  # 2012 and earlier format
        
        # Default to middle format if unclear
        else:
            return 'middle'
    
    def _map_columns_by_format(self, header: list, format_version: str) -> dict:
        """
        Map column names to field names based on detected format version.
        """
        col_mapping = {}
        
        for i, col in enumerate(header):
            col_lower = col.lower().strip()
            
            # Department field (varies by format)
            if col_lower == 'subj' or col_lower == 'dept':
                col_mapping['department'] = i
            
            # Common fields across all formats
            elif col == '#' or col_lower == '#':
                col_mapping['course_number'] = i
            elif col_lower == 'title':
                col_mapping['title'] = i
            elif col_lower == 'comp numb' or 'comp numb' in col_lower:
                col_mapping['crn'] = i
            elif col_lower == 'sec':
                col_mapping['section'] = i
            elif col_lower == 'lec lab' or 'lec lab' in col_lower:
                col_mapping['lec_lab'] = i
            elif col_lower == 'camp code' or 'camp code' in col_lower:
                col_mapping['camp_code'] = i
            elif col_lower == 'max enrollment' or 'max enrollment' in col_lower:
                col_mapping['capacity'] = i
            elif col_lower == 'current enrollment' or 'current enrollment' in col_lower:
                col_mapping['enrollment'] = i
            elif col_lower == 'start time' or 'start time' in col_lower:
                col_mapping['start_time'] = i
            elif col_lower == 'end time' or 'end time' in col_lower:
                col_mapping['end_time'] = i
            elif col_lower == 'days':
                col_mapping['days'] = i
            elif col_lower == 'credits':
                col_mapping['credits'] = i
            elif col_lower == 'bldg':
                col_mapping['building'] = i
            elif col_lower == 'room':
                col_mapping['room'] = i
            elif col_lower == 'instructor':
                col_mapping['instructor'] = i
            
            # Fields that exist in middle and new formats only
            elif col_lower == 'netid' and format_version in ['middle', 'new']:
                col_mapping['netid'] = i
            elif col_lower == 'email' and format_version in ['middle', 'new']:
                col_mapping['email'] = i
            
            # Fields that exist in new format only
            elif format_version == 'new':
                if col_lower == 'ptrm':
                    col_mapping['ptrm'] = i
                elif col_lower == 'attr':
                    col_mapping['attr'] = i
                elif col_lower == 'coll code' or 'coll code' in col_lower:
                    col_mapping['coll_code'] = i
                elif col_lower == 'true max' or 'true max' in col_lower:
                    col_mapping['true_max'] = i
                elif col_lower == 'gp ind' or 'gp ind' in col_lower:
                    col_mapping['gp_ind'] = i
                elif col_lower == 'fees':
                    col_mapping['fees'] = i
                elif col_lower == 'xlistings' or 'xlistings' in col_lower:
                    col_mapping['xlistings'] = i
        
        return col_mapping
        logger.info(f"Parsed {len(courses)} courses for {term} {year}")
        return courses
        
    def _safe_get_field(self, row: list, col_mapping: dict, field_name: str) -> str:
        """Safely extract a field from a CSV row."""
        if field_name not in col_mapping:
            return ''
        col_index = col_mapping[field_name]
        if col_index >= len(row):
            return ''
        return row[col_index].strip('"').strip()
        
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
            # Download CSV data directly instead of HTML
            csv_content = self.get_csv_data(link_info['csv_url'])
            if csv_content:
                courses = self.parse_enrollment_data(
                    csv_content, 
                    link_info['term'], 
                    link_info['year']
                )
                all_courses.extend(courses)
                logger.info(f"Total courses scraped so far: {len(all_courses)}")
                
        logger.info(f"Scraping complete. Total courses: {len(all_courses)}")
        return all_courses
