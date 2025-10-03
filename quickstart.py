#!/usr/bin/env python3
"""
Quick start script for UVM Course-Faculty Enrollment Network Analysis.
This script helps new users get started quickly.
"""

import os
import sys
import subprocess


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70 + "\n")


def run_command(cmd, description):
    """Run a command and display its output."""
    print(f"\n{description}...")
    print(f"Running: {cmd}\n")
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    return result.returncode == 0


def main():
    print_header("UVM Course-Faculty Enrollment Network Analysis - Quick Start")
    
    print("This script will help you get started with the system.")
    print("\nWhat would you like to do?")
    print("\n1. Generate sample data and run analysis")
    print("2. Just generate sample data")
    print("3. Run analysis on existing data")
    print("4. Show database statistics")
    print("5. Run a quick demo query")
    print("6. Exit")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice == "1":
        print_header("Option 1: Generate Sample Data and Run Analysis")
        
        # Generate sample data
        if run_command("python generate_sample_data.py", "Generating sample data"):
            print("\n✓ Sample data generated successfully!")
        else:
            print("\n✗ Failed to generate sample data")
            return
        
        # Run analysis
        if run_command("python main.py analyze", "Running network analysis"):
            print("\n✓ Analysis complete!")
        else:
            print("\n✗ Analysis failed")
            return
        
        # Show stats
        run_command("python main.py stats", "Showing database statistics")
        
        print("\n" + "=" * 70)
        print("Next steps:")
        print("  - Check data/visualizations/ for network diagrams")
        print("  - Check data/networks/ for analysis reports")
        print("  - Run 'python query_database.py departments' to explore data")
        print("  - Run 'python create_visualizations.py --all' for more plots")
        print("=" * 70 + "\n")
        
    elif choice == "2":
        print_header("Option 2: Generate Sample Data")
        
        if run_command("python generate_sample_data.py", "Generating sample data"):
            print("\n✓ Sample data generated successfully!")
            run_command("python main.py stats", "Database statistics")
        else:
            print("\n✗ Failed to generate sample data")
        
    elif choice == "3":
        print_header("Option 3: Run Analysis on Existing Data")
        
        if not os.path.exists("data/uvm_courses.db"):
            print("✗ No database found! Please generate sample data first (option 2).")
            return
        
        if run_command("python main.py analyze", "Running network analysis"):
            print("\n✓ Analysis complete!")
        else:
            print("\n✗ Analysis failed")
        
    elif choice == "4":
        print_header("Option 4: Show Database Statistics")
        
        if not os.path.exists("data/uvm_courses.db"):
            print("✗ No database found! Please generate sample data first (option 2).")
            return
        
        run_command("python main.py stats", "Database statistics")
        
    elif choice == "5":
        print_header("Option 5: Run a Quick Demo Query")
        
        if not os.path.exists("data/uvm_courses.db"):
            print("✗ No database found! Please generate sample data first (option 2).")
            return
        
        print("Running sample queries...\n")
        run_command("python query_database.py departments", "Listing departments")
        run_command("python query_database.py department CS", "CS department statistics")
        
    elif choice == "6":
        print("\nGoodbye!")
        return
    
    else:
        print("\nInvalid choice. Please run the script again.")


if __name__ == "__main__":
    main()
