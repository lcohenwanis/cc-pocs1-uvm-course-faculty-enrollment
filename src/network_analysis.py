"""
Network analysis for UVM course and faculty data.
"""

import networkx as nx
from networkx.algorithms import bipartite
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
import os
import community.community_louvain as community_louvain
from src.database import Database
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NetworkAnalyzer:
    """Analyzes course and faculty networks."""
    
    def __init__(self, db: Database):
        """Initialize with a database connection."""
        self.db = db
        self.ensure_output_dirs()
        
    def ensure_output_dirs(self):
        """Create output directories if they don't exist."""
        os.makedirs(config.NETWORK_OUTPUT_DIR, exist_ok=True)
        os.makedirs(config.VISUALIZATION_OUTPUT_DIR, exist_ok=True)
        
    def build_bipartite_network(self, start_year: int = None, end_year: int = None) -> nx.Graph:
        """
        Build a bipartite network of courses and faculty.
        Nodes are either courses or faculty members.
        Edges connect faculty to courses they teach.
        """
        logger.info(f"Building bipartite network for years {start_year}-{end_year}")
        
        G = nx.Graph()
        
        # Get all course-faculty relationships
        data = self.db.get_all_courses_with_faculty(start_year, end_year)
        
        for record in data:
            course_node = f"course_{record['full_code']}"
            faculty_node = f"faculty_{record['faculty_name']}" if record['faculty_name'] else None
            
            # Add nodes with attributes
            if course_node not in G:
                G.add_node(course_node, 
                          bipartite=0,
                          type='course',
                          code=record['full_code'],
                          title=record['course_title'],
                          dept=record['dept_code'])
                          
            if faculty_node and faculty_node not in G:
                G.add_node(faculty_node,
                          bipartite=1,
                          type='faculty',
                          name=record['faculty_name'])
                          
            # Add edge with weight (number of times taught)
            if faculty_node:
                if G.has_edge(course_node, faculty_node):
                    G[course_node][faculty_node]['weight'] += 1
                else:
                    G.add_edge(course_node, faculty_node, 
                              weight=1,
                              year=record['year'],
                              term=record['term'])
                              
        logger.info(f"Network built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
        
    def build_faculty_collaboration_network(self, start_year: int = None, end_year: int = None) -> nx.Graph:
        """
        Build a network where faculty are connected if they taught the same course.
        This is a projection of the bipartite network onto the faculty nodes.
        """
        logger.info(f"Building faculty collaboration network for years {start_year}-{end_year}")
        
        # First build the bipartite network
        B = self.build_bipartite_network(start_year, end_year)
        
        # Get faculty nodes
        faculty_nodes = {n for n, d in B.nodes(data=True) if d.get('type') == 'faculty'}
        
        # Create projection onto faculty
        G = nx.Graph()
        
        # Add all faculty as nodes
        for node in faculty_nodes:
            G.add_node(node, **B.nodes[node])
            
        # Connect faculty who taught the same course
        for course in B.nodes():
            if B.nodes[course].get('type') == 'course':
                faculty_teaching = list(B.neighbors(course))
                
                # Create edges between all pairs of faculty teaching this course
                for i, f1 in enumerate(faculty_teaching):
                    for f2 in faculty_teaching[i+1:]:
                        if G.has_edge(f1, f2):
                            G[f1][f2]['weight'] += 1
                            G[f1][f2]['courses'].append(course)
                        else:
                            G.add_edge(f1, f2, weight=1, courses=[course])
                            
        logger.info(f"Faculty network built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
        
    def build_course_network(self, start_year: int = None, end_year: int = None) -> nx.Graph:
        """
        Build a network where courses are connected if they share faculty.
        This is a projection of the bipartite network onto the course nodes.
        """
        logger.info(f"Building course network for years {start_year}-{end_year}")
        
        # First build the bipartite network
        B = self.build_bipartite_network(start_year, end_year)
        
        # Get course nodes
        course_nodes = {n for n, d in B.nodes(data=True) if d.get('type') == 'course'}
        
        # Create projection onto courses
        G = nx.Graph()
        
        # Add all courses as nodes
        for node in course_nodes:
            G.add_node(node, **B.nodes[node])
            
        # Connect courses that share faculty
        for faculty in B.nodes():
            if B.nodes[faculty].get('type') == 'faculty':
                courses_taught = list(B.neighbors(faculty))
                
                # Create edges between all pairs of courses taught by this faculty
                for i, c1 in enumerate(courses_taught):
                    for c2 in courses_taught[i+1:]:
                        if G.has_edge(c1, c2):
                            G[c1][c2]['weight'] += 1
                            G[c1][c2]['shared_faculty'].append(faculty)
                        else:
                            G.add_edge(c1, c2, weight=1, shared_faculty=[faculty])
                            
        logger.info(f"Course network built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
        
    def calculate_centrality_measures(self, G: nx.Graph) -> Dict[str, Dict]:
        """Calculate various centrality measures for network nodes."""
        logger.info("Calculating centrality measures...")
        
        centrality = {}
        
        # Degree centrality
        centrality['degree'] = nx.degree_centrality(G)
        
        # Betweenness centrality
        if G.number_of_nodes() < 1000:  # Only for smaller networks (computationally expensive)
            centrality['betweenness'] = nx.betweenness_centrality(G, weight='weight')
        
        # Closeness centrality
        if nx.is_connected(G):
            centrality['closeness'] = nx.closeness_centrality(G)
        else:
            # For disconnected graphs, calculate for largest component
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            centrality['closeness'] = nx.closeness_centrality(subgraph)
            
        # Eigenvector centrality
        try:
            centrality['eigenvector'] = nx.eigenvector_centrality(G, weight='weight', max_iter=1000)
        except:
            logger.warning("Could not calculate eigenvector centrality")
            
        return centrality
        
    def detect_communities(self, G: nx.Graph) -> Dict[str, int]:
        """Detect communities in the network using Louvain method."""
        logger.info("Detecting communities...")
        
        # Convert to undirected if needed
        if G.is_directed():
            G = G.to_undirected()
            
        # Louvain community detection
        communities = community_louvain.best_partition(G, weight='weight')
        
        logger.info(f"Found {len(set(communities.values()))} communities")
        return communities
        
    def analyze_temporal_evolution(self, year_ranges: List[Tuple[int, int]]) -> Dict:
        """
        Analyze how the network evolves over time.
        year_ranges: list of (start_year, end_year) tuples
        """
        logger.info("Analyzing temporal evolution...")
        
        evolution = {
            'periods': [],
            'network_stats': []
        }
        
        for start_year, end_year in year_ranges:
            logger.info(f"Analyzing period {start_year}-{end_year}")
            
            G = self.build_bipartite_network(start_year, end_year)
            
            stats = {
                'period': f"{start_year}-{end_year}",
                'nodes': G.number_of_nodes(),
                'edges': G.number_of_edges(),
                'density': nx.density(G),
                'avg_degree': sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
            }
            
            # Count faculty and courses
            faculty_count = sum(1 for n, d in G.nodes(data=True) if d.get('type') == 'faculty')
            course_count = sum(1 for n, d in G.nodes(data=True) if d.get('type') == 'course')
            
            stats['faculty_count'] = faculty_count
            stats['course_count'] = course_count
            
            evolution['periods'].append(f"{start_year}-{end_year}")
            evolution['network_stats'].append(stats)
            
        return evolution
        
    def identify_interdisciplinary_connections(self, G: nx.Graph = None) -> List[Dict]:
        """
        Identify interdisciplinary connections based on courses from different departments
        sharing faculty or faculty teaching courses in multiple departments.
        """
        logger.info("Identifying interdisciplinary connections...")
        
        if G is None:
            G = self.build_bipartite_network()
            
        interdisciplinary = []
        
        # Find faculty teaching in multiple departments
        for node, data in G.nodes(data=True):
            if data.get('type') == 'faculty':
                courses = list(G.neighbors(node))
                departments = set()
                
                for course in courses:
                    dept = G.nodes[course].get('dept')
                    if dept:
                        departments.add(dept)
                        
                if len(departments) > 1:
                    interdisciplinary.append({
                        'faculty': data.get('name'),
                        'departments': list(departments),
                        'num_departments': len(departments),
                        'num_courses': len(courses)
                    })
                    
        # Sort by number of departments
        interdisciplinary.sort(key=lambda x: x['num_departments'], reverse=True)
        
        logger.info(f"Found {len(interdisciplinary)} faculty with interdisciplinary teaching")
        return interdisciplinary
        
    def visualize_network(self, G: nx.Graph, output_file: str, 
                         title: str = "Network Visualization",
                         node_color_attr: str = None,
                         layout: str = 'spring') -> None:
        """
        Visualize a network and save to file.
        """
        logger.info(f"Creating visualization: {title}")
        
        plt.figure(figsize=(16, 12))
        
        # Choose layout
        if layout == 'spring':
            pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
        elif layout == 'circular':
            pos = nx.circular_layout(G)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G, seed=42)
            
        # Node colors
        if node_color_attr and node_color_attr in nx.get_node_attributes(G, node_color_attr):
            node_colors = [G.nodes[n].get(node_color_attr, 0) for n in G.nodes()]
        else:
            # Color by node type if bipartite
            node_colors = []
            for n in G.nodes():
                if G.nodes[n].get('type') == 'faculty':
                    node_colors.append('lightblue')
                elif G.nodes[n].get('type') == 'course':
                    node_colors.append('lightcoral')
                else:
                    node_colors.append('lightgray')
                    
        # Node sizes based on degree
        node_sizes = [G.degree(n) * 20 + 50 for n in G.nodes()]
        
        # Edge widths based on weight
        edge_weights = [G[u][v].get('weight', 1) for u, v in G.edges()]
        edge_widths = [w * 0.5 for w in edge_weights]
        
        # Draw network
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.7)
        nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.3)
        
        # Only show labels for smaller networks
        if G.number_of_nodes() < 100:
            labels = {}
            for n in G.nodes():
                if G.nodes[n].get('type') == 'faculty':
                    labels[n] = G.nodes[n].get('name', '')[:20]
                elif G.nodes[n].get('type') == 'course':
                    labels[n] = G.nodes[n].get('code', '')
                else:
                    labels[n] = str(n)[:20]
            nx.draw_networkx_labels(G, pos, labels, font_size=8)
            
        plt.title(title, fontsize=16)
        plt.axis('off')
        plt.tight_layout()
        
        output_path = os.path.join(config.VISUALIZATION_OUTPUT_DIR, output_file)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualization saved to {output_path}")
        
    def generate_report(self, output_file: str = "network_analysis_report.txt") -> None:
        """Generate a comprehensive analysis report."""
        logger.info("Generating analysis report...")
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("UVM COURSE AND FACULTY NETWORK ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Database statistics
        stats = self.db.get_statistics()
        report_lines.append("DATABASE STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Departments: {stats['departments']}")
        report_lines.append(f"Total Faculty: {stats['faculty']}")
        report_lines.append(f"Total Courses: {stats['courses']}")
        report_lines.append(f"Total Course Offerings: {stats['offerings']}")
        report_lines.append(f"Total Teaching Assignments: {stats['teaching_assignments']}")
        report_lines.append(f"Year Range: {stats['year_range'][0]} - {stats['year_range'][1]}")
        report_lines.append("")
        
        # Build and analyze full network
        G = self.build_bipartite_network()
        
        report_lines.append("FULL NETWORK STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Nodes: {G.number_of_nodes()}")
        report_lines.append(f"Total Edges: {G.number_of_edges()}")
        report_lines.append(f"Network Density: {nx.density(G):.4f}")
        report_lines.append(f"Average Degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
        report_lines.append("")
        
        # Interdisciplinary analysis
        interdisciplinary = self.identify_interdisciplinary_connections(G)
        report_lines.append("INTERDISCIPLINARY TEACHING")
        report_lines.append("-" * 80)
        report_lines.append(f"Faculty teaching in multiple departments: {len(interdisciplinary)}")
        report_lines.append("\nTop 10 most interdisciplinary faculty:")
        for i, faculty_info in enumerate(interdisciplinary[:10], 1):
            report_lines.append(f"{i}. {faculty_info['faculty']}: {faculty_info['num_departments']} departments, "
                              f"{faculty_info['num_courses']} courses")
            report_lines.append(f"   Departments: {', '.join(faculty_info['departments'])}")
        report_lines.append("")
        
        # Write report
        output_path = os.path.join(config.NETWORK_OUTPUT_DIR, output_file)
        with open(output_path, 'w') as f:
            f.write('\n'.join(report_lines))
            
        logger.info(f"Report saved to {output_path}")
        
        return '\n'.join(report_lines)
