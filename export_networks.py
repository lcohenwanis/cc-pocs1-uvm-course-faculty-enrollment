"""
Export network data to various formats for analysis in other tools.
"""

import sys
import os
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import Database
from src.network_analysis import NetworkAnalyzer
import networkx as nx


def export_to_graphml(G, filename):
    """Export network to GraphML format (for Gephi, Cytoscape)."""
    output_path = os.path.join('data', 'networks', filename)
    nx.write_graphml(G, output_path)
    print(f"Exported to GraphML: {output_path}")


def export_to_gexf(G, filename):
    """Export network to GEXF format (for Gephi)."""
    output_path = os.path.join('data', 'networks', filename)
    nx.write_gexf(G, output_path)
    print(f"Exported to GEXF: {output_path}")


def export_to_json(G, filename):
    """Export network to JSON format."""
    output_path = os.path.join('data', 'networks', filename)
    data = nx.node_link_data(G)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Exported to JSON: {output_path}")


def export_to_edgelist(G, filename):
    """Export network to edge list format."""
    output_path = os.path.join('data', 'networks', filename)
    nx.write_edgelist(G, output_path, data=['weight'])
    print(f"Exported to edge list: {output_path}")


def export_to_csv(G, prefix):
    """Export network to CSV files (nodes and edges)."""
    import pandas as pd
    
    # Export nodes
    nodes_data = []
    for node, attrs in G.nodes(data=True):
        node_dict = {'node_id': node}
        node_dict.update(attrs)
        nodes_data.append(node_dict)
    
    nodes_df = pd.DataFrame(nodes_data)
    nodes_path = os.path.join('data', 'networks', f'{prefix}_nodes.csv')
    nodes_df.to_csv(nodes_path, index=False)
    print(f"Exported nodes to CSV: {nodes_path}")
    
    # Export edges
    edges_data = []
    for u, v, attrs in G.edges(data=True):
        edge_dict = {'source': u, 'target': v}
        edge_dict.update(attrs)
        edges_data.append(edge_dict)
    
    edges_df = pd.DataFrame(edges_data)
    edges_path = os.path.join('data', 'networks', f'{prefix}_edges.csv')
    edges_df.to_csv(edges_path, index=False)
    print(f"Exported edges to CSV: {edges_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Export network data to various formats'
    )
    
    parser.add_argument(
        'network_type',
        choices=['bipartite', 'faculty', 'course'],
        help='Type of network to export'
    )
    
    parser.add_argument(
        'format',
        choices=['graphml', 'gexf', 'json', 'edgelist', 'csv'],
        help='Export format'
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
    
    print(f"Building {args.network_type} network...")
    
    with Database() as db:
        analyzer = NetworkAnalyzer(db)
        
        if args.network_type == 'bipartite':
            G = analyzer.build_bipartite_network(args.start_year, args.end_year)
            prefix = 'bipartite'
        elif args.network_type == 'faculty':
            G = analyzer.build_faculty_collaboration_network(args.start_year, args.end_year)
            prefix = 'faculty_collaboration'
        else:  # course
            G = analyzer.build_course_network(args.start_year, args.end_year)
            prefix = 'course'
    
    print(f"Network has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Add year range to filename if specified
    if args.start_year and args.end_year:
        prefix = f"{prefix}_{args.start_year}_{args.end_year}"
    
    # Export based on format
    if args.format == 'graphml':
        export_to_graphml(G, f'{prefix}.graphml')
    elif args.format == 'gexf':
        export_to_gexf(G, f'{prefix}.gexf')
    elif args.format == 'json':
        export_to_json(G, f'{prefix}.json')
    elif args.format == 'edgelist':
        export_to_edgelist(G, f'{prefix}.edgelist')
    elif args.format == 'csv':
        export_to_csv(G, prefix)
    
    print("Export complete!")


if __name__ == '__main__':
    main()
