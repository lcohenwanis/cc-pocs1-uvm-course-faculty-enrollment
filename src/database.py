"""
Database schema and models for UVM course enrollment data.
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any
import config


class Database:
    """Manages SQLite database for course enrollment data."""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        self.db_path = db_path or config.DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        
    def create_tables(self):
        """Create database tables if they don't exist."""
        
        # Departments table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT
            )
        ''')
        
        # Faculty table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS faculty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT,
                UNIQUE(normalized_name)
            )
        ''')
        
        # Courses table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_id INTEGER,
                course_number TEXT NOT NULL,
                course_title TEXT,
                full_code TEXT,
                FOREIGN KEY (department_id) REFERENCES departments(id),
                UNIQUE(full_code)
            )
        ''')
        
        # Course offerings table (tracks specific offerings by term)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_offerings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                term TEXT NOT NULL,
                year INTEGER NOT NULL,
                section TEXT,
                crn TEXT,
                enrollment INTEGER,
                capacity INTEGER,
                waitlist INTEGER,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                UNIQUE(course_id, term, year, section)
            )
        ''')
        
        # Faculty teaching assignments
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS teaching_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offering_id INTEGER NOT NULL,
                faculty_id INTEGER NOT NULL,
                is_primary BOOLEAN DEFAULT 1,
                FOREIGN KEY (offering_id) REFERENCES course_offerings(id),
                FOREIGN KEY (faculty_id) REFERENCES faculty(id),
                UNIQUE(offering_id, faculty_id)
            )
        ''')
        
        # Create indexes for better query performance
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_course_offerings_year 
            ON course_offerings(year)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_course_offerings_term 
            ON course_offerings(term)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_teaching_assignments_faculty 
            ON teaching_assignments(faculty_id)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_teaching_assignments_offering 
            ON teaching_assignments(offering_id)
        ''')
        
        self.conn.commit()
        
    def insert_department(self, code: str, name: str = None) -> int:
        """Insert a department and return its ID."""
        try:
            self.cursor.execute(
                'INSERT INTO departments (code, name) VALUES (?, ?)',
                (code, name)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Department already exists, get its ID
            self.cursor.execute('SELECT id FROM departments WHERE code = ?', (code,))
            return self.cursor.fetchone()[0]
            
    def insert_faculty(self, name: str, normalized_name: str = None) -> int:
        """Insert a faculty member and return their ID."""
        if normalized_name is None:
            normalized_name = name.lower().strip()
            
        try:
            self.cursor.execute(
                'INSERT INTO faculty (name, normalized_name) VALUES (?, ?)',
                (name, normalized_name)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Faculty already exists, get their ID
            self.cursor.execute('SELECT id FROM faculty WHERE normalized_name = ?', (normalized_name,))
            return self.cursor.fetchone()[0]
            
    def insert_course(self, department_id: int, course_number: str, 
                      course_title: str = None, full_code: str = None) -> int:
        """Insert a course and return its ID."""
        if full_code is None:
            full_code = f"{department_id}-{course_number}"
            
        try:
            self.cursor.execute(
                'INSERT INTO courses (department_id, course_number, course_title, full_code) VALUES (?, ?, ?, ?)',
                (department_id, course_number, course_title, full_code)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Course already exists, get its ID
            self.cursor.execute('SELECT id FROM courses WHERE full_code = ?', (full_code,))
            return self.cursor.fetchone()[0]
            
    def insert_course_offering(self, course_id: int, term: str, year: int,
                               section: str = None, crn: str = None,
                               enrollment: int = None, capacity: int = None,
                               waitlist: int = None) -> int:
        """Insert a course offering and return its ID."""
        try:
            self.cursor.execute('''
                INSERT INTO course_offerings 
                (course_id, term, year, section, crn, enrollment, capacity, waitlist)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (course_id, term, year, section, crn, enrollment, capacity, waitlist))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Offering already exists, get its ID
            self.cursor.execute('''
                SELECT id FROM course_offerings 
                WHERE course_id = ? AND term = ? AND year = ? AND section = ?
            ''', (course_id, term, year, section))
            return self.cursor.fetchone()[0]
            
    def insert_teaching_assignment(self, offering_id: int, faculty_id: int,
                                   is_primary: bool = True) -> int:
        """Insert a teaching assignment and return its ID."""
        try:
            self.cursor.execute('''
                INSERT INTO teaching_assignments (offering_id, faculty_id, is_primary)
                VALUES (?, ?, ?)
            ''', (offering_id, faculty_id, is_primary))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Assignment already exists
            self.cursor.execute('''
                SELECT id FROM teaching_assignments 
                WHERE offering_id = ? AND faculty_id = ?
            ''', (offering_id, faculty_id))
            result = self.cursor.fetchone()
            return result[0] if result else None
            
    def get_all_courses_with_faculty(self, start_year: int = None, end_year: int = None) -> List[Dict]:
        """Get all courses with their faculty assignments."""
        query = '''
            SELECT 
                c.full_code, c.course_title, c.course_number,
                d.code as dept_code, d.name as dept_name,
                co.term, co.year, co.section,
                f.name as faculty_name, f.normalized_name,
                co.enrollment, co.capacity
            FROM courses c
            JOIN departments d ON c.department_id = d.id
            JOIN course_offerings co ON c.id = co.course_id
            LEFT JOIN teaching_assignments ta ON co.id = ta.offering_id
            LEFT JOIN faculty f ON ta.faculty_id = f.id
        '''
        
        conditions = []
        params = []
        
        if start_year is not None:
            conditions.append('co.year >= ?')
            params.append(start_year)
            
        if end_year is not None:
            conditions.append('co.year <= ?')
            params.append(end_year)
            
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
            
        query += ' ORDER BY co.year, co.term, c.full_code'
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        self.cursor.execute('SELECT COUNT(*) FROM departments')
        stats['departments'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM faculty')
        stats['faculty'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM courses')
        stats['courses'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM course_offerings')
        stats['offerings'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM teaching_assignments')
        stats['teaching_assignments'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT MIN(year), MAX(year) FROM course_offerings')
        year_range = self.cursor.fetchone()
        stats['year_range'] = (year_range[0], year_range[1])
        
        return stats
