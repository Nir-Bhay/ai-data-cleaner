"""Quick check script to test Flask app"""
import sys
import traceback

with open("check_output.txt", "w") as f:
    try:
        f.write("Step 1: Importing Flask modules...\n")
        from flask import Flask
        f.write("  Flask imported OK\n")
        
        f.write("Step 2: Importing app...\n")
        from app import app
        f.write("  App imported OK\n")
        
        f.write("Step 3: Testing modules...\n")
        from modules.csv_loader import load_csv
        f.write("  csv_loader OK\n")
        
        from modules.rule_parser import parse_rules
        f.write("  rule_parser OK\n")
        
        from modules.data_cleaner import clean_data
        f.write("  data_cleaner OK\n")
        
        from modules.db_manager import init_database
        f.write("  db_manager OK\n")
        
        f.write("\nAll imports successful!\n")
        f.write("Ready to run: python app.py\n")
        
    except Exception as e:
        f.write(f"\nERROR: {e}\n")
        f.write(traceback.format_exc())

print("Check complete - see check_output.txt")
