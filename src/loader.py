"""
Data loader to process scraped enrollment data into the database.
"""

import logging
from typing import List, Dict
from src.database import Database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataLoader:
    """Loads scraped course data into the database."""
    
    def __init__(self, db: Database):
        """Initialize with a database connection."""
        self.db = db
        
    def normalize_instructor_name(self, name: str) -> str:
        """Normalize instructor names for consistent storage."""
        if not name or name.lower() in ['tba', 'staff', 'tbd', '']:
            return 'TBA'
            
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Convert to title case
        name = name.title()
        
        return name
        
    def parse_instructor_list(self, instructor_str: str) -> List[str]:
        """Parse a string that may contain multiple instructors."""
        if not instructor_str:
            return ['TBA']
            
        # Split on common delimiters
        instructors = []
        for delimiter in [',', ';', '/', ' and ', ' & ']:
            if delimiter in instructor_str:
                parts = instructor_str.split(delimiter)
                instructors = [self.normalize_instructor_name(p) for p in parts]
                break
                
        if not instructors:
            instructors = [self.normalize_instructor_name(instructor_str)]
            
        return [i for i in instructors if i]
        
    def load_course_record(self, record: Dict) -> bool:
        """
        Load a single course record into the database.
        Returns True if successful, False otherwise.
        """
        try:
            # Extract and validate required fields
            dept_code = record.get('department', '').strip().upper()
            course_number = record.get('course_number', '').strip()
            term = record.get('term', '').strip()
            year = record.get('year')
            
            if not dept_code or not course_number or not term or not year:
                logger.debug(f"Skipping incomplete record: {record}")
                return False
                
            # Insert department
            dept_id = self.db.insert_department(dept_code)
            
            # Insert course
            course_title = record.get('title', '').strip()
            full_code = f"{dept_code} {course_number}"
            course_id = self.db.insert_course(
                dept_id, 
                course_number, 
                course_title, 
                full_code
            )
            
            # Insert course offering
            section = record.get('section', '').strip() or '01'
            crn = record.get('crn', '').strip()
            enrollment = record.get('enrollment')
            capacity = record.get('capacity')
            waitlist = record.get('waitlist')
            
            offering_id = self.db.insert_course_offering(
                course_id, term, year, section, crn,
                enrollment, capacity, waitlist
            )
            
            # Insert faculty teaching assignments
            instructor_str = record.get('instructor', '')
            instructors = self.parse_instructor_list(instructor_str)
            
            for i, instructor in enumerate(instructors):
                faculty_id = self.db.insert_faculty(
                    instructor, 
                    instructor.lower()
                )
                
                # First instructor is primary
                is_primary = (i == 0)
                self.db.insert_teaching_assignment(
                    offering_id, 
                    faculty_id, 
                    is_primary
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Error loading record {record}: {e}")
            return False
            
    def load_all_records(self, records: List[Dict]) -> Dict[str, int]:
        """
        Load all records into the database.
        Returns statistics about the loading process.
        """
        stats = {
            'total': len(records),
            'successful': 0,
            'failed': 0
        }
        
        logger.info(f"Loading {stats['total']} records into database...")
        
        for i, record in enumerate(records):
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{stats['total']} records")
                
            if self.load_course_record(record):
                stats['successful'] += 1
            else:
                stats['failed'] += 1
                
        self.db.conn.commit()
        
        logger.info(f"Loading complete: {stats['successful']} successful, {stats['failed']} failed")
        return stats
