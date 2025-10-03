# UVM Course-Faculty Enrollment Network Analysis

A comprehensive Python system for scraping, storing, and analyzing UVM course enrollment data from 1995-2025. This project constructs bipartite and multilayer networks of courses and faculty across time to explore how disciplines evolve, identify interdisciplinary connections, and analyze the centrality of departments and faculty roles.

## Features

- **Web Scraping**: Automated scraping of course enrollment data from UVM's enrollment website
- **SQLite Database**: Structured storage of courses, faculty, departments, and teaching assignments
- **Network Analysis**: Construction and analysis of:
  - Bipartite networks (courses and faculty)
  - Faculty collaboration networks
  - Course networks (connected by shared faculty)
- **Temporal Analysis**: Track network evolution over time periods
- **Interdisciplinary Detection**: Identify faculty teaching across multiple departments
- **Centrality Measures**: Calculate degree, betweenness, closeness, and eigenvector centrality
- **Community Detection**: Identify communities using the Louvain method
- **Visualizations**: Generate network visualizations and analysis reports

## Project Structure

```
.
├── main.py                      # Main orchestration script
├── config.py                    # Configuration settings
├── requirements.txt             # Python dependencies
├── generate_sample_data.py      # Sample data generator for testing
├── query_database.py            # Database query utility
├── export_networks.py           # Network export utility
├── create_visualizations.py     # Visualization generation script
├── src/
│   ├── __init__.py             # Package initialization
│   ├── database.py             # Database schema and operations
│   ├── scraper.py              # Web scraping functionality
│   ├── loader.py               # Data loading into database
│   └── network_analysis.py     # Network construction and analysis
└── data/                        # Data storage directory
    ├── uvm_courses.db          # SQLite database
    ├── networks/               # Network data files
    └── visualizations/         # Network visualization images

```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/lcohenwanis/cc-pocs1-uvm-course-faculty-enrollment.git
cd cc-pocs1-uvm-course-faculty-enrollment
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start with Sample Data

Generate and analyze sample data to test the system:

```bash
# Generate sample data and load into database
python generate_sample_data.py

# Analyze the network
python main.py analyze

# Query the database
python query_database.py departments

# Export networks for external analysis
python export_networks.py faculty csv
```

### Full Pipeline

To scrape real data from the UVM website and perform analysis:

```bash
# Run the complete pipeline (scrape, load, and analyze)
python main.py full

# Or run steps individually:

# 1. Initialize the database
python main.py setup

# 2. Scrape enrollment data from the web
python main.py scrape

# 3. Perform network analysis
python main.py analyze
```

### Commands

- `setup`: Initialize the database and create tables
- `scrape`: Scrape enrollment data from the UVM website and load into database
- `analyze`: Perform network analysis on existing database
- `full`: Run the complete pipeline (setup + scrape + analyze)
- `stats`: Display database statistics

### Options

```bash
# Analyze specific year range
python main.py analyze --start-year 2015 --end-year 2020

# Scrape specific year range
python main.py scrape --start-year 2015 --end-year 2020
```

## Configuration

Edit `config.py` to customize:

- Data source URL
- Year range for scraping (START_YEAR, END_YEAR)
- Database location
- Network output directories
- Scraping delays and timeouts

## Utility Scripts

### Query Database (`query_database.py`)

Interactive database queries:

```bash
# List all departments
python query_database.py departments

# Show department statistics
python query_database.py department CS

# Search for faculty
python query_database.py faculty "Smith"

# Search for courses
python query_database.py courses "Machine Learning"

# Show courses taught by a faculty member
python query_database.py faculty-courses "John Smith"

# Show instructors for a course
python query_database.py course-instructors "CS 101"
```

### Export Networks (`export_networks.py`)

Export network data for analysis in other tools (Gephi, Cytoscape, R, etc.):

```bash
# Export faculty collaboration network to CSV
python export_networks.py faculty csv

# Export bipartite network to GraphML (for Gephi)
python export_networks.py bipartite graphml

# Export course network to GEXF
python export_networks.py course gexf

# Export with year filtering
python export_networks.py faculty json --start-year 2015 --end-year 2020
```

Supported formats:
- `csv`: Node and edge CSV files (great for spreadsheet analysis)
- `graphml`: GraphML format (Gephi, Cytoscape, yEd)
- `gexf`: GEXF format (Gephi)
- `json`: JSON format (web applications, custom tools)
- `edgelist`: Simple edge list (many graph tools)

### Create Visualizations (`create_visualizations.py`)

Generate comprehensive visualizations and plots:

```bash
# Create all visualizations
python create_visualizations.py --all

# Create specific visualizations
python create_visualizations.py --temporal
python create_visualizations.py --distribution
python create_visualizations.py --interdisciplinary

# Create temporal plots for specific year range
python create_visualizations.py --temporal --start-year 2015 --end-year 2020
```

Generated visualizations include:
- Department distribution plots (courses and faculty per department)
- Interdisciplinary analysis (faculty teaching across departments)
- Temporal evolution (network metrics over time)
- Network diagrams (bipartite, faculty collaboration, course networks)

## Database Schema

The SQLite database contains the following tables:

- **departments**: Department codes and names
- **faculty**: Faculty members with normalized names
- **courses**: Course information (department, number, title)
- **course_offerings**: Specific course offerings by term and year
- **teaching_assignments**: Links between faculty and course offerings

## Network Analysis

The system performs several types of network analysis:

### 1. Bipartite Network
- Nodes: Courses and faculty members
- Edges: Teaching relationships
- Analysis: Identifies connections between courses and instructors

### 2. Faculty Collaboration Network
- Nodes: Faculty members
- Edges: Shared teaching of courses
- Analysis: Reveals collaboration patterns and interdisciplinary teaching

### 3. Course Network
- Nodes: Courses
- Edges: Shared faculty members
- Analysis: Shows course relationships and potential interdisciplinary fields

### Metrics Calculated

- **Degree Centrality**: Identifies most connected faculty/courses
- **Betweenness Centrality**: Finds faculty/courses that bridge different areas
- **Closeness Centrality**: Measures how central a node is in the network
- **Community Detection**: Groups related courses or faculty
- **Temporal Evolution**: Tracks network changes over time

## Output

The analysis generates:

1. **Network Visualizations** (PNG files in `data/visualizations/`)
   - Bipartite network diagram
   - Faculty collaboration network
   - Course network

2. **Analysis Report** (`data/networks/network_analysis_report.txt`)
   - Database statistics
   - Network metrics
   - Interdisciplinary faculty rankings
   - Community detection results

3. **Console Output**
   - Real-time progress updates
   - Key findings and statistics
   - Top faculty by centrality measures

## Data Source

The system is designed to scrape data from:
https://serval.uvm.edu/~rgweb/batch/enrollment/enrollment_tab.html

The scraper is flexible and can be adapted to different HTML structures by modifying the parsing logic in `src/scraper.py`.

## Example Analysis Questions

This system can help answer questions like:

- Which faculty members teach across the most departments?
- How have interdisciplinary connections evolved over time?
- What are the most central courses in the curriculum?
- Which departments are most interconnected?
- How do faculty collaboration networks change over time?
- What communities of related courses exist?

## Development

### Adding New Analysis

To add new network analysis features:

1. Add methods to the `NetworkAnalyzer` class in `src/network_analysis.py`
2. Update the `analyze_network()` function in `main.py` to call your new methods
3. Update the report generation to include new findings

### Customizing the Scraper

To adapt the scraper to different data sources:

1. Modify `get_enrollment_links()` in `src/scraper.py` to match the link structure
2. Update `parse_enrollment_data()` to match the data format
3. Adjust field mappings in the parsing logic

## Requirements

- Python 3.7+
- See `requirements.txt` for package dependencies

## License

This project is for academic research purposes.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

Data source: University of Vermont Registrar's Office