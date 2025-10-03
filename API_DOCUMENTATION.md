# API Documentation

This document provides detailed information about the modules and classes in the UVM Course-Faculty Enrollment Network Analysis system.

## Module Overview

- `src.database` - Database operations and schema management
- `src.scraper` - Web scraping functionality
- `src.loader` - Data loading and processing
- `src.network_analysis` - Network construction and analysis

## src.database

### Database Class

Main database management class.

#### Methods

##### `__init__(db_path: str = None)`
Initialize database connection.

**Parameters:**
- `db_path` (str, optional): Path to SQLite database file. Defaults to config.DATABASE_PATH.

##### `create_tables()`
Create all database tables and indexes.

##### `insert_department(code: str, name: str = None) -> int`
Insert a department record.

**Parameters:**
- `code` (str): Department code (e.g., 'CS', 'MATH')
- `name` (str, optional): Full department name

**Returns:**
- int: Department ID

##### `insert_faculty(name: str, normalized_name: str = None) -> int`
Insert a faculty member.

**Parameters:**
- `name` (str): Faculty name
- `normalized_name` (str, optional): Normalized version for deduplication

**Returns:**
- int: Faculty ID

##### `insert_course(department_id: int, course_number: str, course_title: str = None, full_code: str = None) -> int`
Insert a course record.

**Parameters:**
- `department_id` (int): Foreign key to departments table
- `course_number` (str): Course number (e.g., '101', '301')
- `course_title` (str, optional): Course title
- `full_code` (str, optional): Full course code (e.g., 'CS 101')

**Returns:**
- int: Course ID

##### `insert_course_offering(course_id: int, term: str, year: int, section: str = None, ...) -> int`
Insert a course offering record.

**Parameters:**
- `course_id` (int): Foreign key to courses table
- `term` (str): Term (e.g., 'Fall', 'Spring')
- `year` (int): Year
- `section` (str, optional): Section number
- `crn` (str, optional): Course registration number
- `enrollment` (int, optional): Number of enrolled students
- `capacity` (int, optional): Course capacity
- `waitlist` (int, optional): Waitlist count

**Returns:**
- int: Course offering ID

##### `insert_teaching_assignment(offering_id: int, faculty_id: int, is_primary: bool = True) -> int`
Insert a teaching assignment linking faculty to a course offering.

**Parameters:**
- `offering_id` (int): Foreign key to course_offerings table
- `faculty_id` (int): Foreign key to faculty table
- `is_primary` (bool, optional): Whether this is the primary instructor

**Returns:**
- int: Assignment ID

##### `get_all_courses_with_faculty(start_year: int = None, end_year: int = None) -> List[Dict]`
Retrieve all course offerings with faculty information.

**Parameters:**
- `start_year` (int, optional): Filter by start year
- `end_year` (int, optional): Filter by end year

**Returns:**
- List[Dict]: List of course records with faculty information

##### `get_statistics() -> Dict[str, Any]`
Get database statistics.

**Returns:**
- Dict containing counts of departments, faculty, courses, offerings, and assignments

## src.scraper

### EnrollmentScraper Class

Web scraper for UVM course enrollment data.

#### Methods

##### `__init__(base_url: str = None)`
Initialize the scraper.

**Parameters:**
- `base_url` (str, optional): Base URL for enrollment data. Defaults to config.BASE_URL.

##### `get_page(url: str) -> Optional[str]`
Fetch a web page.

**Parameters:**
- `url` (str): URL to fetch

**Returns:**
- str: HTML content or None if error

##### `get_enrollment_links() -> List[Dict[str, str]]`
Parse the main enrollment page to find links to data files.

**Returns:**
- List[Dict]: List of dicts with 'url', 'term', 'year' keys

##### `parse_enrollment_data(html: str, term: str, year: int) -> List[Dict]`
Parse enrollment data from HTML.

**Parameters:**
- `html` (str): HTML content
- `term` (str): Term name
- `year` (int): Year

**Returns:**
- List[Dict]: List of course records

##### `scrape_all() -> List[Dict]`
Scrape all enrollment data within configured year range.

**Returns:**
- List[Dict]: All course records

## src.loader

### DataLoader Class

Loads scraped course data into the database.

#### Methods

##### `__init__(db: Database)`
Initialize with database connection.

**Parameters:**
- `db` (Database): Database instance

##### `normalize_instructor_name(name: str) -> str`
Normalize instructor names for consistency.

**Parameters:**
- `name` (str): Original instructor name

**Returns:**
- str: Normalized name

##### `parse_instructor_list(instructor_str: str) -> List[str]`
Parse string containing multiple instructors.

**Parameters:**
- `instructor_str` (str): String with one or more instructor names

**Returns:**
- List[str]: List of individual instructor names

##### `load_course_record(record: Dict) -> bool`
Load a single course record into database.

**Parameters:**
- `record` (Dict): Course record dictionary

**Returns:**
- bool: True if successful

##### `load_all_records(records: List[Dict]) -> Dict[str, int]`
Load all records into database.

**Parameters:**
- `records` (List[Dict]): List of course records

**Returns:**
- Dict: Statistics about loading process

## src.network_analysis

### NetworkAnalyzer Class

Analyzes course and faculty networks.

#### Methods

##### `__init__(db: Database)`
Initialize with database connection.

**Parameters:**
- `db` (Database): Database instance

##### `build_bipartite_network(start_year: int = None, end_year: int = None) -> nx.Graph`
Build bipartite network of courses and faculty.

**Parameters:**
- `start_year` (int, optional): Filter by start year
- `end_year` (int, optional): Filter by end year

**Returns:**
- nx.Graph: NetworkX graph with bipartite structure

##### `build_faculty_collaboration_network(start_year: int = None, end_year: int = None) -> nx.Graph`
Build network of faculty connected by shared courses.

**Parameters:**
- `start_year` (int, optional): Filter by start year
- `end_year` (int, optional): Filter by end year

**Returns:**
- nx.Graph: Faculty collaboration network

##### `build_course_network(start_year: int = None, end_year: int = None) -> nx.Graph`
Build network of courses connected by shared faculty.

**Parameters:**
- `start_year` (int, optional): Filter by start year
- `end_year` (int, optional): Filter by end year

**Returns:**
- nx.Graph: Course network

##### `calculate_centrality_measures(G: nx.Graph) -> Dict[str, Dict]`
Calculate various centrality measures.

**Parameters:**
- `G` (nx.Graph): NetworkX graph

**Returns:**
- Dict: Dictionary of centrality measures (degree, betweenness, closeness, eigenvector)

##### `detect_communities(G: nx.Graph) -> Dict[str, int]`
Detect communities using Louvain method.

**Parameters:**
- `G` (nx.Graph): NetworkX graph

**Returns:**
- Dict: Mapping of nodes to community IDs

##### `analyze_temporal_evolution(year_ranges: List[Tuple[int, int]]) -> Dict`
Analyze network evolution over time periods.

**Parameters:**
- `year_ranges` (List[Tuple]): List of (start_year, end_year) tuples

**Returns:**
- Dict: Evolution statistics for each period

##### `identify_interdisciplinary_connections(G: nx.Graph = None) -> List[Dict]`
Identify faculty teaching across multiple departments.

**Parameters:**
- `G` (nx.Graph, optional): Bipartite network. If None, builds one.

**Returns:**
- List[Dict]: List of interdisciplinary faculty with statistics

##### `visualize_network(G: nx.Graph, output_file: str, title: str = "Network Visualization", ...)`
Create and save network visualization.

**Parameters:**
- `G` (nx.Graph): NetworkX graph
- `output_file` (str): Output filename
- `title` (str, optional): Plot title
- `node_color_attr` (str, optional): Node attribute for coloring
- `layout` (str, optional): Layout algorithm ('spring', 'circular', 'kamada_kawai')

##### `generate_report(output_file: str = "network_analysis_report.txt") -> str`
Generate comprehensive analysis report.

**Parameters:**
- `output_file` (str, optional): Output filename

**Returns:**
- str: Report content

## Example Usage

### Basic Database Operations

```python
from src.database import Database

with Database() as db:
    # Create tables
    db.create_tables()
    
    # Insert data
    dept_id = db.insert_department('CS', 'Computer Science')
    faculty_id = db.insert_faculty('John Smith')
    course_id = db.insert_course(dept_id, '101', 'Intro to Programming')
    offering_id = db.insert_course_offering(course_id, 'Fall', 2024)
    db.insert_teaching_assignment(offering_id, faculty_id)
    
    # Get statistics
    stats = db.get_statistics()
    print(stats)
```

### Network Analysis

```python
from src.database import Database
from src.network_analysis import NetworkAnalyzer

with Database() as db:
    analyzer = NetworkAnalyzer(db)
    
    # Build networks
    bipartite = analyzer.build_bipartite_network(2020, 2024)
    faculty_net = analyzer.build_faculty_collaboration_network(2020, 2024)
    
    # Analyze
    centrality = analyzer.calculate_centrality_measures(faculty_net)
    interdisciplinary = analyzer.identify_interdisciplinary_connections()
    
    # Visualize
    analyzer.visualize_network(faculty_net, "faculty_network.png")
    
    # Generate report
    report = analyzer.generate_report()
```

### Web Scraping and Loading

```python
from src.database import Database
from src.scraper import EnrollmentScraper
from src.loader import DataLoader

# Scrape data
scraper = EnrollmentScraper()
courses = scraper.scrape_all()

# Load into database
with Database() as db:
    db.create_tables()
    loader = DataLoader(db)
    stats = loader.load_all_records(courses)
    print(f"Loaded {stats['successful']} records")
```

## Configuration

All configuration options are in `config.py`:

- `BASE_URL`: URL of enrollment data source
- `START_YEAR`, `END_YEAR`: Year range for scraping
- `DATABASE_PATH`: Path to SQLite database
- `NETWORK_OUTPUT_DIR`: Directory for network data exports
- `VISUALIZATION_OUTPUT_DIR`: Directory for visualizations
- `REQUEST_TIMEOUT`: HTTP request timeout in seconds
- `DELAY_BETWEEN_REQUESTS`: Delay between HTTP requests
