"""
Sample data generator for testing the UVM enrollment system.
Creates synthetic enrollment data that mimics the structure of real data.
"""

import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import Database
from src.loader import DataLoader


# Sample departments
DEPARTMENTS = [
    'MATH', 'CS', 'STAT', 'PHYS', 'CHEM', 'BIOL', 
    'ENGL', 'HIST', 'PSYC', 'ECON', 'POLS', 'SOC',
    'ENGR', 'MUS', 'ART', 'THTR', 'PHIL', 'LING'
]

# Sample faculty names
FACULTY_NAMES = [
    'Smith, John', 'Johnson, Mary', 'Williams, Robert', 'Brown, Jennifer',
    'Jones, Michael', 'Garcia, Sarah', 'Miller, David', 'Davis, Lisa',
    'Rodriguez, Carlos', 'Martinez, Anna', 'Hernandez, James', 'Lopez, Emily',
    'Gonzalez, Thomas', 'Wilson, Patricia', 'Anderson, Christopher', 'Thomas, Linda',
    'Taylor, Daniel', 'Moore, Nancy', 'Jackson, Paul', 'Martin, Karen',
    'Lee, Mark', 'Perez, Susan', 'Thompson, Steven', 'White, Betty',
    'Harris, Edward', 'Sanchez, Dorothy', 'Clark, Brian', 'Ramirez, Sandra',
    'Lewis, Kevin', 'Robinson, Ashley', 'Walker, Jason', 'Young, Melissa',
    'Allen, Matthew', 'King, Laura', 'Wright, Ryan', 'Scott, Michelle',
    'Green, Justin', 'Baker, Rebecca', 'Adams, Eric', 'Nelson, Kimberly',
    'Hill, Andrew', 'Flores, Jessica', 'Mitchell, Joshua', 'Roberts, Amanda',
    'Carter, Nicholas', 'Phillips, Stephanie', 'Evans, Brandon', 'Turner, Nicole'
]

# Sample course titles by department
COURSE_TITLES = {
    'MATH': ['Calculus I', 'Calculus II', 'Linear Algebra', 'Differential Equations', 
             'Statistics', 'Discrete Mathematics', 'Abstract Algebra', 'Real Analysis'],
    'CS': ['Intro to Programming', 'Data Structures', 'Algorithms', 'Database Systems',
           'Operating Systems', 'Computer Networks', 'Artificial Intelligence', 'Machine Learning'],
    'STAT': ['Intro to Statistics', 'Probability Theory', 'Statistical Inference', 'Regression Analysis',
             'Time Series', 'Experimental Design', 'Bayesian Statistics', 'Data Mining'],
    'PHYS': ['General Physics I', 'General Physics II', 'Mechanics', 'Electromagnetism',
             'Quantum Mechanics', 'Thermodynamics', 'Modern Physics', 'Astrophysics'],
    'CHEM': ['General Chemistry I', 'General Chemistry II', 'Organic Chemistry I', 'Organic Chemistry II',
             'Physical Chemistry', 'Analytical Chemistry', 'Biochemistry', 'Inorganic Chemistry'],
    'BIOL': ['General Biology I', 'General Biology II', 'Cell Biology', 'Genetics',
             'Ecology', 'Evolution', 'Molecular Biology', 'Microbiology'],
}

# Default titles for other departments
DEFAULT_TITLES = ['Introduction to {}', 'Advanced {}', 'Topics in {}', 'Seminar in {}']

TERMS = ['Fall', 'Spring', 'Summer']


def generate_course_title(dept):
    """Generate a course title for a given department."""
    if dept in COURSE_TITLES:
        return random.choice(COURSE_TITLES[dept])
    else:
        template = random.choice(DEFAULT_TITLES)
        return template.format(dept)


def generate_sample_data(start_year=2015, end_year=2024, courses_per_term=50):
    """Generate sample enrollment data."""
    records = []
    
    for year in range(start_year, end_year + 1):
        for term in TERMS:
            if term == 'Summer' and random.random() < 0.5:
                continue  # Skip some summer terms
                
            for _ in range(courses_per_term):
                dept = random.choice(DEPARTMENTS)
                course_num = random.randint(100, 499)
                section = random.choice(['01', '02', '03'])
                
                # Probability of having co-instructors
                num_instructors = 1 if random.random() < 0.85 else 2
                instructors = random.sample(FACULTY_NAMES, num_instructors)
                instructor_str = ' & '.join(instructors)
                
                enrollment = random.randint(5, 150)
                capacity = enrollment + random.randint(0, 20)
                
                record = {
                    'department': dept,
                    'course_number': str(course_num),
                    'section': section,
                    'title': generate_course_title(dept),
                    'instructor': instructor_str,
                    'term': term,
                    'year': year,
                    'enrollment': enrollment,
                    'capacity': capacity,
                    'crn': f"{year}{random.randint(10000, 99999)}"
                }
                
                records.append(record)
    
    return records


def load_sample_data():
    """Generate and load sample data into the database."""
    print("Generating sample data...")
    records = generate_sample_data(start_year=2015, end_year=2024, courses_per_term=50)
    print(f"Generated {len(records)} sample records")
    
    print("\nInitializing database...")
    with Database() as db:
        db.create_tables()
        
        print("Loading data into database...")
        loader = DataLoader(db)
        stats = loader.load_all_records(records)
        
    print(f"\nLoading complete!")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    
    print("\nDatabase statistics:")
    with Database() as db:
        db_stats = db.get_statistics()
        
    print(f"  Departments: {db_stats['departments']}")
    print(f"  Faculty: {db_stats['faculty']}")
    print(f"  Courses: {db_stats['courses']}")
    print(f"  Course Offerings: {db_stats['offerings']}")
    print(f"  Teaching Assignments: {db_stats['teaching_assignments']}")
    print(f"  Year Range: {db_stats['year_range'][0]} - {db_stats['year_range'][1]}")


if __name__ == '__main__':
    load_sample_data()
