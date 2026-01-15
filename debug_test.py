import sys
import traceback

outfile = open("debug_output.txt", "w")

try:
    outfile.write("Step 1: Checking imports...\n")
    sys.path.insert(0, ".")
    
    outfile.write("Step 2: Importing csv_loader...\n")
    from modules.csv_loader import load_csv
    outfile.write("  OK\n")
    
    outfile.write("Step 3: Loading CSV...\n")
    df = load_csv("tests/sample_data.csv")
    outfile.write(f"  Loaded {len(df)} rows\n")
    
    outfile.write("Step 4: Importing rule_parser...\n")
    from modules.rule_parser import parse_rules
    outfile.write("  OK\n")
    
    outfile.write("Step 5: Parsing rules...\n")
    result = parse_rules("Remove duplicates", df.columns.tolist())
    outfile.write(f"  Found {len(result['rules'])} rules\n")
    
    outfile.write("\nSUCCESS!\n")
    
except Exception as e:
    outfile.write(f"\nERROR: {e}\n")
    outfile.write(traceback.format_exc())

outfile.close()
print("Done - check debug_output.txt")
