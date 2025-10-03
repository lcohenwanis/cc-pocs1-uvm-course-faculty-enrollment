"""
Query script for exploring the UVM course enrollment database.
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import Database


def list_departments(db):
    """List all departments."""
    db.cursor.execute('SELECT code, name FROM departments ORDER BY code')
    results = db.cursor.fetchall()
    
    print("\nDEPARTMENTS")
    print("-" * 60)
    for row in results:
        code, name = row
        print(f"{code:6} {name or 'N/A'}")
    print(f"\nTotal: {len(results)} departments")


def search_faculty(db, name_pattern):
    """Search for faculty by name."""
    db.cursor.execute(
        'SELECT id, name FROM faculty WHERE name LIKE ? ORDER BY name',
        (f'%{name_pattern}%',)
    )
    results = db.cursor.fetchall()
    
    print(f"\nFACULTY matching '{name_pattern}'")
    print("-" * 60)
    for row in results:
        fid, name = row
        
        # Count courses taught
        db.cursor.execute('''
            SELECT COUNT(DISTINCT co.course_id)
            FROM teaching_assignments ta
            JOIN course_offerings co ON ta.offering_id = co.id
            WHERE ta.faculty_id = ?
        ''', (fid,))
        course_count = db.cursor.fetchone()[0]
        
        # Get departments
        db.cursor.execute('''
            SELECT DISTINCT d.code
            FROM teaching_assignments ta
            JOIN course_offerings co ON ta.offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            JOIN departments d ON c.department_id = d.id
            WHERE ta.faculty_id = ?
            ORDER BY d.code
        ''', (fid,))
        depts = [row[0] for row in db.cursor.fetchall()]
        
        print(f"{name:30} | Courses: {course_count:3} | Depts: {', '.join(depts)}")
    
    print(f"\nTotal: {len(results)} faculty found")


def search_courses(db, pattern):
    """Search for courses by code or title."""
    db.cursor.execute('''
        SELECT c.full_code, c.course_title, d.code, COUNT(co.id) as offerings
        FROM courses c
        JOIN departments d ON c.department_id = d.id
        LEFT JOIN course_offerings co ON c.id = co.course_id
        WHERE c.full_code LIKE ? OR c.course_title LIKE ?
        GROUP BY c.id
        ORDER BY c.full_code
    ''', (f'%{pattern}%', f'%{pattern}%'))
    results = db.cursor.fetchall()
    
    print(f"\nCOURSES matching '{pattern}'")
    print("-" * 80)
    for row in results:
        code, title, dept, offerings = row
        print(f"{code:15} {dept:6} {title:40} ({offerings} offerings)")
    
    print(f"\nTotal: {len(results)} courses found")


def faculty_courses(db, faculty_name):
    """Show all courses taught by a faculty member."""
    db.cursor.execute(
        'SELECT id, name FROM faculty WHERE name LIKE ? LIMIT 1',
        (f'%{faculty_name}%',)
    )
    result = db.cursor.fetchone()
    
    if not result:
        print(f"Faculty '{faculty_name}' not found")
        return
    
    fid, name = result
    
    print(f"\nCOURSES TAUGHT BY: {name}")
    print("-" * 80)
    
    db.cursor.execute('''
        SELECT c.full_code, c.course_title, co.term, co.year, co.enrollment
        FROM teaching_assignments ta
        JOIN course_offerings co ON ta.offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        WHERE ta.faculty_id = ?
        ORDER BY co.year DESC, co.term, c.full_code
    ''', (fid,))
    
    results = db.cursor.fetchall()
    
    for row in results:
        code, title, term, year, enrollment = row
        enr = enrollment if enrollment else '?'
        print(f"{year} {term:6} {code:15} {title:40} (Enr: {enr})")
    
    print(f"\nTotal: {len(results)} course offerings")


def course_instructors(db, course_code):
    """Show all instructors who taught a course."""
    db.cursor.execute(
        'SELECT id, full_code, course_title FROM courses WHERE full_code LIKE ? LIMIT 1',
        (f'%{course_code}%',)
    )
    result = db.cursor.fetchone()
    
    if not result:
        print(f"Course '{course_code}' not found")
        return
    
    cid, code, title = result
    
    print(f"\nINSTRUCTORS FOR: {code} - {title}")
    print("-" * 80)
    
    db.cursor.execute('''
        SELECT DISTINCT f.name, COUNT(co.id) as times_taught, 
               MIN(co.year) as first_year, MAX(co.year) as last_year
        FROM teaching_assignments ta
        JOIN course_offerings co ON ta.offering_id = co.id
        JOIN faculty f ON ta.faculty_id = f.id
        WHERE co.course_id = ?
        GROUP BY f.id
        ORDER BY times_taught DESC, f.name
    ''', (cid,))
    
    results = db.cursor.fetchall()
    
    for row in results:
        name, times, first, last = row
        years = f"{first}-{last}" if first != last else str(first)
        print(f"{name:30} | Times taught: {times:3} | Years: {years}")
    
    print(f"\nTotal: {len(results)} instructors")


def department_stats(db, dept_code):
    """Show statistics for a department."""
    db.cursor.execute('SELECT id, code, name FROM departments WHERE code = ?', (dept_code.upper(),))
    result = db.cursor.fetchone()
    
    if not result:
        print(f"Department '{dept_code}' not found")
        return
    
    did, code, name = result
    
    print(f"\nDEPARTMENT STATISTICS: {code}")
    if name:
        print(f"Name: {name}")
    print("-" * 60)
    
    # Count courses
    db.cursor.execute('SELECT COUNT(*) FROM courses WHERE department_id = ?', (did,))
    course_count = db.cursor.fetchone()[0]
    
    # Count offerings
    db.cursor.execute('''
        SELECT COUNT(*) FROM course_offerings co
        JOIN courses c ON co.course_id = c.id
        WHERE c.department_id = ?
    ''', (did,))
    offering_count = db.cursor.fetchone()[0]
    
    # Count faculty
    db.cursor.execute('''
        SELECT COUNT(DISTINCT ta.faculty_id)
        FROM teaching_assignments ta
        JOIN course_offerings co ON ta.offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        WHERE c.department_id = ?
    ''', (did,))
    faculty_count = db.cursor.fetchone()[0]
    
    # Get year range
    db.cursor.execute('''
        SELECT MIN(co.year), MAX(co.year)
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.id
        WHERE c.department_id = ?
    ''', (did,))
    year_range = db.cursor.fetchone()
    
    print(f"Courses: {course_count}")
    print(f"Course Offerings: {offering_count}")
    print(f"Faculty: {faculty_count}")
    print(f"Year Range: {year_range[0]} - {year_range[1]}")


def main():
    parser = argparse.ArgumentParser(
        description='Query the UVM course enrollment database'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Query command')
    
    # List departments
    subparsers.add_parser('departments', help='List all departments')
    
    # Search faculty
    faculty_parser = subparsers.add_parser('faculty', help='Search for faculty')
    faculty_parser.add_argument('name', help='Faculty name or pattern')
    
    # Search courses
    course_parser = subparsers.add_parser('courses', help='Search for courses')
    course_parser.add_argument('pattern', help='Course code or title pattern')
    
    # Faculty courses
    faculty_courses_parser = subparsers.add_parser('faculty-courses', help='Show courses taught by faculty')
    faculty_courses_parser.add_argument('name', help='Faculty name')
    
    # Course instructors
    course_inst_parser = subparsers.add_parser('course-instructors', help='Show instructors for a course')
    course_inst_parser.add_argument('code', help='Course code')
    
    # Department stats
    dept_parser = subparsers.add_parser('department', help='Show department statistics')
    dept_parser.add_argument('code', help='Department code')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    with Database() as db:
        if args.command == 'departments':
            list_departments(db)
        elif args.command == 'faculty':
            search_faculty(db, args.name)
        elif args.command == 'courses':
            search_courses(db, args.pattern)
        elif args.command == 'faculty-courses':
            faculty_courses(db, args.name)
        elif args.command == 'course-instructors':
            course_instructors(db, args.code)
        elif args.command == 'department':
            department_stats(db, args.code)


if __name__ == '__main__':
    main()
