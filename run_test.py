"""
Quick test script for the data cleaning system.
Runs and outputs results to a file.
"""
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

# Output file
output_file = Path(__file__).parent / "test_output.txt"

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("DATA CLEANING SYSTEM TEST\n")
    f.write("=" * 60 + "\n\n")
    
    try:
        # Test 1: Load CSV
        f.write("TEST 1: Loading CSV...\n")
        from modules.csv_loader import load_csv, get_csv_info
        df = load_csv("tests/sample_data.csv")
        info = get_csv_info(df)
        f.write(f"  ✓ Loaded {info['rows']} rows, {info['columns']} columns\n")
        f.write(f"  Columns: {info['column_names']}\n")
        f.write(f"  Duplicates: {info['duplicate_rows']}\n\n")
        
        # Test 2: Parse rules
        f.write("TEST 2: Parsing rules...\n")
        from modules.rule_parser import parse_rules
        prompt = "Remove duplicates and fill missing age values with the mean"
        result = parse_rules(prompt, df.columns.tolist())
        f.write(f"  Parser: {result['parser_used']}\n")
        f.write(f"  Rules found: {len(result['rules'])}\n")
        for i, rule in enumerate(result['rules'], 1):
            f.write(f"    {i}. {rule['action']}: {rule.get('params', {})}\n")
        f.write("\n")
        
        # Test 3: Clean data
        f.write("TEST 3: Cleaning data...\n")
        from modules.data_cleaner import clean_data
        rows_before = len(df)
        cleaned_df, actions = clean_data(df, result['rules'])
        rows_after = len(cleaned_df)
        f.write(f"  Rows: {rows_before} → {rows_after}\n")
        for action in actions:
            f.write(f"    • {action}\n")
        f.write("\n")
        
        # Test 4: Save to database
        f.write("TEST 4: Saving to database...\n")
        from modules.db_manager import save_dataset, list_datasets
        dataset_id = save_dataset(
            df=cleaned_df,
            original_filename="sample_data.csv",
            user_prompt=prompt,
            rules=result['rules'],
            parser_used=result['parser_used'],
            rows_before=rows_before,
            actions_log=actions
        )
        f.write(f"  ✓ Saved with ID: {dataset_id}\n\n")
        
        # Test 5: List datasets
        f.write("TEST 5: Listing datasets...\n")
        datasets = list_datasets()
        f.write(f"  Total datasets: {len(datasets)}\n")
        for ds in datasets:
            f.write(f"    - ID {ds['id']}: {ds['original_filename']} ({ds['rows_count']} rows)\n")
        f.write("\n")
        
        # Test 6: Export
        f.write("TEST 6: Exporting for Power BI...\n")
        from modules.db_manager import export_for_powerbi
        export_path = export_for_powerbi(dataset_id, "data/exports/test_export.csv")
        f.write(f"  ✓ Exported to: {export_path}\n\n")
        
        f.write("=" * 60 + "\n")
        f.write("ALL TESTS PASSED! ✅\n")
        f.write("=" * 60 + "\n")
        
    except Exception as e:
        import traceback
        f.write(f"\n❌ ERROR: {e}\n")
        f.write(traceback.format_exc())

print("Test complete. Check test_output.txt")
