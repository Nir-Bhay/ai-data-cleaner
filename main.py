"""
AI-Assisted Data Cleaning System
================================
CLI interface for cleaning CSV data using natural language instructions.

Usage:
    python main.py clean <csv_file> --prompt "your cleaning instructions"
    python main.py history
    python main.py show <dataset_id>
    python main.py export <dataset_id> --output <path>
"""
import argparse
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.csv_loader import load_csv, validate_csv, print_csv_summary, get_csv_info
from modules.rule_parser import parse_rules, print_rules
from modules.data_cleaner import clean_data
from modules.db_manager import (
    init_database, save_dataset, get_dataset, list_datasets,
    get_metadata, export_for_powerbi, delete_dataset
)
from config import EXPORTS_DIR, GEMINI_API_KEY


def banner():
    """Print application banner."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║       AI-ASSISTED DATA CLEANING SYSTEM                        ║
║       Clean your data with natural language instructions      ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def cmd_clean(args):
    """
    Clean a CSV file based on natural language instructions.
    
    Args:
        args: Command line arguments with csv_file and prompt
    """
    csv_path = args.csv_file
    prompt = args.prompt
    
    print(f"\n📂 Loading CSV file: {csv_path}")
    print("=" * 60)
    
    # Step 1: Load CSV
    try:
        df = load_csv(csv_path)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {csv_path}")
        return 1
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return 1
    
    # Step 2: Validate and show summary
    is_valid, issues = validate_csv(df)
    if not is_valid:
        print("\n⚠️  Validation warnings:")
        for issue in issues:
            print(f"   - {issue}")
    
    print_csv_summary(df)
    rows_before = len(df)
    
    # Step 3: Parse cleaning instructions
    print(f"\n📝 Parsing cleaning instructions...")
    print(f"   Prompt: \"{prompt}\"")
    print("-" * 60)
    
    columns = df.columns.tolist()
    rules_result = parse_rules(prompt, columns)
    print_rules(rules_result)
    
    if not rules_result['rules']:
        print("\n⚠️  No cleaning rules were detected from your prompt.")
        print("   Try being more specific, e.g.:")
        print("   - 'Remove duplicate rows'")
        print("   - 'Fill missing values in age column with mean'")
        print("   - 'Remove rows where age < 18'")
        return 1
    
    # Step 4: Apply cleaning rules
    print(f"\n🧹 Applying cleaning rules...")
    print("-" * 60)
    
    cleaned_df, actions_log = clean_data(df, rules_result['rules'])
    
    rows_after = len(cleaned_df)
    print("\n" + "=" * 60)
    print(f"✓ Cleaning complete!")
    print(f"   Rows: {rows_before:,} → {rows_after:,} ({rows_before - rows_after:,} removed)")
    print(f"   Columns: {len(cleaned_df.columns)}")
    
    # Step 5: Save to database
    print(f"\n💾 Saving to database...")
    print("-" * 60)
    
    try:
        dataset_id = save_dataset(
            df=cleaned_df,
            original_filename=Path(csv_path).name,
            user_prompt=prompt,
            rules=rules_result['rules'],
            parser_used=rules_result['parser_used'],
            rows_before=rows_before,
            actions_log=actions_log
        )
        
        print(f"\n✅ Success! Dataset saved with ID: {dataset_id}")
        print(f"\nNext steps:")
        print(f"   • View dataset: python main.py show {dataset_id}")
        print(f"   • Export for Power BI: python main.py export {dataset_id} --output cleaned_data.csv")
        
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        return 1
    
    return 0


def cmd_history(args):
    """
    Show all cleaned datasets.
    """
    print("\n📊 Cleaning History")
    print("=" * 80)
    
    datasets = list_datasets()
    
    if not datasets:
        print("No datasets found. Clean a CSV file first:")
        print("  python main.py clean data.csv --prompt \"your instructions\"")
        return 0
    
    print(f"{'ID':<5} {'Original File':<25} {'Rows':<10} {'Created':<20} {'Parser':<10}")
    print("-" * 80)
    
    for ds in datasets:
        created = ds.get('created_at', 'N/A')
        if created and 'T' in str(created):
            created = str(created).split('T')[0]
        
        print(f"{ds['id']:<5} {str(ds['original_filename'])[:24]:<25} "
              f"{ds['rows_count']:<10} {str(created)[:19]:<20} {ds.get('parser_used', 'N/A'):<10}")
    
    print("-" * 80)
    print(f"Total: {len(datasets)} datasets\n")
    
    return 0


def cmd_show(args):
    """
    Show details of a specific dataset.
    """
    dataset_id = args.dataset_id
    
    print(f"\n📋 Dataset Details (ID: {dataset_id})")
    print("=" * 60)
    
    # Get metadata
    metadata = get_metadata(dataset_id)
    
    if not metadata:
        print(f"❌ Dataset with ID {dataset_id} not found.")
        return 1
    
    print(f"Original File: {metadata['original_filename']}")
    print(f"Table Name: {metadata['table_name']}")
    print(f"Created: {metadata['created_at']}")
    print(f"Parser Used: {metadata.get('parser_used', 'N/A')}")
    print(f"Rows (before → after): {metadata.get('rows_before', 'N/A')} → {metadata['rows_count']}")
    print(f"Columns: {metadata['columns_count']}")
    
    print(f"\n📝 User Prompt:")
    print(f"   \"{metadata.get('user_prompt', 'N/A')}\"")
    
    if metadata.get('applied_rules'):
        print(f"\n🔧 Applied Rules:")
        for i, rule in enumerate(metadata['applied_rules'], 1):
            print(f"   {i}. {rule.get('action')} - {rule.get('params', {})}")
    
    if metadata.get('actions_log'):
        print(f"\n📜 Actions Log:")
        for action in metadata['actions_log']:
            print(f"   • {action}")
    
    # Show sample data
    df = get_dataset(dataset_id)
    if df is not None:
        print(f"\n📊 Data Preview (first 5 rows):")
        print("-" * 60)
        print(df.head().to_string())
    
    print("\n" + "=" * 60)
    return 0


def cmd_export(args):
    """
    Export a dataset to CSV for Power BI.
    """
    dataset_id = args.dataset_id
    output_path = args.output
    
    # Default output path if not provided
    if not output_path:
        output_path = str(EXPORTS_DIR / f"dataset_{dataset_id}_export.csv")
    
    print(f"\n📤 Exporting Dataset {dataset_id}")
    print("=" * 60)
    
    try:
        exported_path = export_for_powerbi(dataset_id, output_path)
        print(f"\n✅ Export successful!")
        print(f"   File: {exported_path}")
        print(f"\n💡 Open this file in Power BI Desktop to analyze your data.")
        return 0
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return 1


def cmd_delete(args):
    """
    Delete a dataset.
    """
    dataset_id = args.dataset_id
    
    if not args.force:
        confirm = input(f"Are you sure you want to delete dataset {dataset_id}? (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return 0
    
    if delete_dataset(dataset_id):
        print(f"✅ Dataset {dataset_id} deleted.")
        return 0
    else:
        print(f"❌ Dataset {dataset_id} not found.")
        return 1


def main():
    """Main entry point."""
    banner()
    
    # Check for Gemini API key
    if not GEMINI_API_KEY:
        print("⚠️  Note: GEMINI_API_KEY not set. Using pattern-based parsing.")
        print("   Set the key: set GEMINI_API_KEY=your_key_here")
        print()
    
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="AI-Assisted Data Cleaning System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py clean data.csv --prompt "Remove duplicates and fill missing ages with mean"
  python main.py history
  python main.py show 1
  python main.py export 1 --output cleaned_data.csv
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean a CSV file')
    clean_parser.add_argument('csv_file', help='Path to the CSV file')
    clean_parser.add_argument('--prompt', '-p', required=True, help='Natural language cleaning instructions')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show cleaning history')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show dataset details')
    show_parser.add_argument('dataset_id', type=int, help='Dataset ID')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export dataset for Power BI')
    export_parser.add_argument('dataset_id', type=int, help='Dataset ID')
    export_parser.add_argument('--output', '-o', help='Output file path')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a dataset')
    delete_parser.add_argument('dataset_id', type=int, help='Dataset ID')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'clean':
        return cmd_clean(args)
    elif args.command == 'history':
        return cmd_history(args)
    elif args.command == 'show':
        return cmd_show(args)
    elif args.command == 'export':
        return cmd_export(args)
    elif args.command == 'delete':
        return cmd_delete(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
