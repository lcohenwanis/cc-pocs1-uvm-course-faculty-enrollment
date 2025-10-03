"""
Create comprehensive visualizations of network data.
"""

import sys
import os
import argparse
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import Database
from src.network_analysis import NetworkAnalyzer


def plot_temporal_evolution(analyzer, year_ranges):
    """Create plots showing network evolution over time."""
    evolution = analyzer.analyze_temporal_evolution(year_ranges)
    
    periods = evolution['periods']
    stats = evolution['network_stats']
    
    # Extract metrics
    faculty_counts = [s['faculty_count'] for s in stats]
    course_counts = [s['course_count'] for s in stats]
    densities = [s['density'] for s in stats]
    avg_degrees = [s['avg_degree'] for s in stats]
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Faculty and course counts
    x = range(len(periods))
    ax1.plot(x, faculty_counts, 'o-', label='Faculty', linewidth=2, markersize=8)
    ax1.plot(x, course_counts, 's-', label='Courses', linewidth=2, markersize=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(periods, rotation=45, ha='right')
    ax1.set_ylabel('Count')
    ax1.set_title('Faculty and Courses Over Time', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Network density
    ax2.plot(x, densities, 'o-', color='green', linewidth=2, markersize=8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(periods, rotation=45, ha='right')
    ax2.set_ylabel('Density')
    ax2.set_title('Network Density Over Time', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Average degree
    ax3.plot(x, avg_degrees, 'o-', color='red', linewidth=2, markersize=8)
    ax3.set_xticks(x)
    ax3.set_xticklabels(periods, rotation=45, ha='right')
    ax3.set_ylabel('Average Degree')
    ax3.set_title('Average Node Degree Over Time', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Total nodes and edges
    total_nodes = [s['nodes'] for s in stats]
    total_edges = [s['edges'] for s in stats]
    
    ax4_twin = ax4.twinx()
    line1 = ax4.plot(x, total_nodes, 'o-', label='Nodes', linewidth=2, markersize=8, color='blue')
    line2 = ax4_twin.plot(x, total_edges, 's-', label='Edges', linewidth=2, markersize=8, color='orange')
    ax4.set_xticks(x)
    ax4.set_xticklabels(periods, rotation=45, ha='right')
    ax4.set_ylabel('Nodes', color='blue')
    ax4_twin.set_ylabel('Edges', color='orange')
    ax4.set_title('Total Nodes and Edges Over Time', fontsize=14, fontweight='bold')
    ax4.tick_params(axis='y', labelcolor='blue')
    ax4_twin.tick_params(axis='y', labelcolor='orange')
    ax4.grid(True, alpha=0.3)
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax4.legend(lines, labels, loc='upper left')
    
    plt.tight_layout()
    output_path = os.path.join('data', 'visualizations', 'temporal_evolution.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Temporal evolution plot saved to {output_path}")


def plot_department_distribution(db):
    """Create plots showing distribution of courses and faculty by department."""
    # Get courses per department
    db.cursor.execute('''
        SELECT d.code, COUNT(DISTINCT c.id) as course_count
        FROM departments d
        LEFT JOIN courses c ON d.id = c.department_id
        GROUP BY d.id
        ORDER BY course_count DESC
    ''')
    dept_courses = db.cursor.fetchall()
    
    # Get faculty per department
    db.cursor.execute('''
        SELECT d.code, COUNT(DISTINCT ta.faculty_id) as faculty_count
        FROM departments d
        LEFT JOIN courses c ON d.id = c.department_id
        LEFT JOIN course_offerings co ON c.id = co.course_id
        LEFT JOIN teaching_assignments ta ON co.id = ta.offering_id
        GROUP BY d.id
        ORDER BY faculty_count DESC
    ''')
    dept_faculty = db.cursor.fetchall()
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Courses per department
    depts1, counts1 = zip(*dept_courses)
    ax1.barh(depts1, counts1, color='steelblue')
    ax1.set_xlabel('Number of Courses')
    ax1.set_title('Courses by Department', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='x')
    
    # Plot 2: Faculty per department
    depts2, counts2 = zip(*dept_faculty)
    ax2.barh(depts2, counts2, color='coral')
    ax2.set_xlabel('Number of Faculty')
    ax2.set_title('Faculty by Department', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    output_path = os.path.join('data', 'visualizations', 'department_distribution.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Department distribution plot saved to {output_path}")


def plot_interdisciplinary_stats(analyzer):
    """Create plots showing interdisciplinary connections."""
    G = analyzer.build_bipartite_network()
    interdisciplinary = analyzer.identify_interdisciplinary_connections(G)
    
    if not interdisciplinary:
        print("No interdisciplinary data found")
        return
    
    # Get top 20 for visualization
    top_interdisciplinary = interdisciplinary[:20]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot 1: Top interdisciplinary faculty by department count
    names = [f['faculty'][:20] for f in top_interdisciplinary]
    dept_counts = [f['num_departments'] for f in top_interdisciplinary]
    
    y_pos = np.arange(len(names))
    ax1.barh(y_pos, dept_counts, color='mediumseagreen')
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names)
    ax1.invert_yaxis()
    ax1.set_xlabel('Number of Departments')
    ax1.set_title('Top 20 Interdisciplinary Faculty\n(by Department Count)', 
                  fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='x')
    
    # Plot 2: Distribution of interdisciplinarity
    dept_count_distribution = {}
    for f in interdisciplinary:
        count = f['num_departments']
        dept_count_distribution[count] = dept_count_distribution.get(count, 0) + 1
    
    counts = sorted(dept_count_distribution.keys())
    frequencies = [dept_count_distribution[c] for c in counts]
    
    ax2.bar(counts, frequencies, color='mediumpurple', alpha=0.7)
    ax2.set_xlabel('Number of Departments Taught In')
    ax2.set_ylabel('Number of Faculty')
    ax2.set_title('Distribution of Interdisciplinary Teaching', 
                  fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_path = os.path.join('data', 'visualizations', 'interdisciplinary_analysis.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Interdisciplinary analysis plot saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Create comprehensive visualizations of the network'
    )
    
    parser.add_argument(
        '--temporal',
        action='store_true',
        help='Create temporal evolution plots'
    )
    
    parser.add_argument(
        '--distribution',
        action='store_true',
        help='Create department distribution plots'
    )
    
    parser.add_argument(
        '--interdisciplinary',
        action='store_true',
        help='Create interdisciplinary analysis plots'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Create all visualizations'
    )
    
    parser.add_argument(
        '--start-year',
        type=int,
        help='Start year for filtering data'
    )
    
    parser.add_argument(
        '--end-year',
        type=int,
        help='End year for filtering data'
    )
    
    args = parser.parse_args()
    
    # If no specific plots requested, create all
    if not (args.temporal or args.distribution or args.interdisciplinary):
        args.all = True
    
    with Database() as db:
        analyzer = NetworkAnalyzer(db)
        
        if args.all or args.distribution:
            print("\nCreating department distribution plots...")
            plot_department_distribution(db)
        
        if args.all or args.interdisciplinary:
            print("\nCreating interdisciplinary analysis plots...")
            plot_interdisciplinary_stats(analyzer)
        
        if args.all or args.temporal:
            print("\nCreating temporal evolution plots...")
            # Define periods for temporal analysis
            start = args.start_year or 2015
            end = args.end_year or 2024
            year_ranges = [(y, min(y+4, end)) for y in range(start, end, 5)]
            
            if year_ranges:
                plot_temporal_evolution(analyzer, year_ranges)
    
    print("\nAll visualizations complete!")


if __name__ == '__main__':
    main()
