"""
Main script to orchestrate the entire UVM course enrollment data pipeline.
"""

import argparse
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import Database
from src.scraper import EnrollmentScraper
from src.loader import DataLoader
from src.network_analysis import NetworkAnalyzer
import config

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('uvm_enrollment.log')
    ]
)
logger = logging.getLogger(__name__)


def setup_database():
    """Initialize database and create tables."""
    logger.info("Setting up database...")
    with Database() as db:
        db.create_tables()
    logger.info("Database setup complete")


def scrape_data():
    """Scrape enrollment data from the web."""
    logger.info("Starting data scraping...")
    scraper = EnrollmentScraper()
    
    try:
        courses = scraper.scrape_all()
        logger.info(f"Scraped {len(courses)} course records")
        return courses
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        return []


def load_data(courses):
    """Load scraped data into the database."""
    logger.info("Loading data into database...")
    
    with Database() as db:
        loader = DataLoader(db)
        stats = loader.load_all_records(courses)
        
    logger.info(f"Data loading complete: {stats}")
    return stats


def analyze_network(start_year=None, end_year=None):
    """Perform network analysis."""
    logger.info("Starting network analysis...")
    
    with Database() as db:
        analyzer = NetworkAnalyzer(db)
        
        # Generate comprehensive report
        report = analyzer.generate_report()
        print("\n" + report)
        
        # Build various networks
        logger.info("Building bipartite network...")
        bipartite_net = analyzer.build_bipartite_network(start_year, end_year)
        
        logger.info("Building faculty collaboration network...")
        faculty_net = analyzer.build_faculty_collaboration_network(start_year, end_year)
        
        logger.info("Building course network...")
        course_net = analyzer.build_course_network(start_year, end_year)
        
        # Visualize networks (only if not too large)
        if bipartite_net.number_of_nodes() < 500:
            analyzer.visualize_network(
                bipartite_net, 
                "bipartite_network.png",
                "Course-Faculty Bipartite Network"
            )
        
        if faculty_net.number_of_nodes() < 300:
            analyzer.visualize_network(
                faculty_net,
                "faculty_collaboration_network.png",
                "Faculty Collaboration Network"
            )
            
        if course_net.number_of_nodes() < 300:
            analyzer.visualize_network(
                course_net,
                "course_network.png",
                "Course Network (Connected by Shared Faculty)"
            )
        
        # Temporal analysis - analyze by 5-year periods
        if start_year and end_year:
            periods = [(y, min(y+4, end_year)) for y in range(start_year, end_year, 5)]
            evolution = analyzer.analyze_temporal_evolution(periods)
            
            logger.info("\nTemporal Evolution:")
            for stat in evolution['network_stats']:
                logger.info(f"\nPeriod {stat['period']}:")
                logger.info(f"  Faculty: {stat['faculty_count']}, Courses: {stat['course_count']}")
                logger.info(f"  Nodes: {stat['nodes']}, Edges: {stat['edges']}")
                logger.info(f"  Density: {stat['density']:.4f}, Avg Degree: {stat['avg_degree']:.2f}")
        
        # Calculate centrality for faculty network
        if faculty_net.number_of_nodes() > 0 and faculty_net.number_of_nodes() < 1000:
            logger.info("Calculating centrality measures...")
            centrality = analyzer.calculate_centrality_measures(faculty_net)
            
            # Report top faculty by degree centrality
            if 'degree' in centrality:
                top_faculty = sorted(centrality['degree'].items(), key=lambda x: x[1], reverse=True)[:10]
                logger.info("\nTop 10 Faculty by Degree Centrality:")
                for i, (faculty, score) in enumerate(top_faculty, 1):
                    faculty_name = faculty_net.nodes[faculty].get('name', faculty)
                    logger.info(f"{i}. {faculty_name}: {score:.4f}")
        
        # Detect communities in faculty network
        if faculty_net.number_of_nodes() > 0 and faculty_net.number_of_nodes() < 1000:
            logger.info("Detecting communities...")
            communities = analyzer.detect_communities(faculty_net)
            logger.info(f"Detected {len(set(communities.values()))} communities")
    
    logger.info("Network analysis complete")


def show_statistics():
    """Display database statistics."""
    with Database() as db:
        stats = db.get_statistics()
        
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    print(f"Departments:          {stats['departments']}")
    print(f"Faculty:              {stats['faculty']}")
    print(f"Courses:              {stats['courses']}")
    print(f"Course Offerings:     {stats['offerings']}")
    print(f"Teaching Assignments: {stats['teaching_assignments']}")
    print(f"Year Range:           {stats['year_range'][0]} - {stats['year_range'][1]}")
    print("=" * 60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='UVM Course Enrollment Data Scraper and Network Analyzer'
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'scrape', 'analyze', 'full', 'stats'],
        help='Command to execute: setup (initialize DB), scrape (download data), '
             'analyze (perform network analysis), full (run entire pipeline), '
             'stats (show database statistics)'
    )
    
    parser.add_argument(
        '--start-year',
        type=int,
        default=config.START_YEAR,
        help=f'Start year for analysis (default: {config.START_YEAR})'
    )
    
    parser.add_argument(
        '--end-year',
        type=int,
        default=config.END_YEAR,
        help=f'End year for analysis (default: {config.END_YEAR})'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'setup':
            setup_database()
            
        elif args.command == 'scrape':
            setup_database()
            courses = scrape_data()
            if courses:
                load_data(courses)
            else:
                logger.warning("No courses scraped. Check the scraper configuration.")
                
        elif args.command == 'analyze':
            analyze_network(args.start_year, args.end_year)
            
        elif args.command == 'full':
            # Run complete pipeline
            setup_database()
            courses = scrape_data()
            if courses:
                load_data(courses)
                analyze_network(args.start_year, args.end_year)
            else:
                logger.warning("No courses scraped. Skipping analysis.")
                
        elif args.command == 'stats':
            show_statistics()
            
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
