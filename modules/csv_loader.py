"""
CSV Loader Module
-----------------
Handles loading, validating, and analyzing CSV files.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DEFAULT_ENCODING, FALLBACK_ENCODINGS, MAX_FILE_SIZE_MB


def load_csv(filepath: str, encoding: Optional[str] = None) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.
    
    Tries multiple encodings if the default fails.
    
    Args:
        filepath: Path to the CSV file
        encoding: Optional specific encoding to use
        
    Returns:
        pandas DataFrame with the loaded data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is too large or can't be read
    """
    path = Path(filepath)
    
    # Check if file exists
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    # Check file size
    file_size_mb = path.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {file_size_mb:.2f}MB (max: {MAX_FILE_SIZE_MB}MB)")
    
    # Try to load with specified or default encoding
    encodings_to_try = [encoding] if encoding else [DEFAULT_ENCODING] + FALLBACK_ENCODINGS
    
    last_error = None
    for enc in encodings_to_try:
        if enc is None:
            continue
        try:
            df = pd.read_csv(filepath, encoding=enc)
            print(f"✓ Successfully loaded CSV with encoding: {enc}")
            return df
        except UnicodeDecodeError as e:
            last_error = e
            continue
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
    
    raise ValueError(f"Could not read CSV with any encoding. Last error: {last_error}")


def validate_csv(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate a loaded DataFrame for common issues.
    
    Args:
        df: pandas DataFrame to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check if DataFrame is empty
    if df.empty:
        issues.append("DataFrame is empty (no rows)")
    
    # Check for completely empty columns
    empty_cols = df.columns[df.isna().all()].tolist()
    if empty_cols:
        issues.append(f"Completely empty columns: {empty_cols}")
    
    # Check for duplicate column names
    if df.columns.duplicated().any():
        dup_cols = df.columns[df.columns.duplicated()].tolist()
        issues.append(f"Duplicate column names: {dup_cols}")
    
    # Check for unnamed columns
    unnamed = [col for col in df.columns if 'Unnamed' in str(col)]
    if unnamed:
        issues.append(f"Unnamed columns detected: {unnamed}")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def get_csv_info(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get detailed information about a DataFrame.
    
    Args:
        df: pandas DataFrame to analyze
        
    Returns:
        Dictionary with DataFrame information
    """
    # Count missing values per column (convert to native Python int)
    missing_counts = {k: int(v) for k, v in df.isna().sum().to_dict().items()}
    missing_percent = {k: float(v) for k, v in ((df.isna().sum() / len(df)) * 100).round(2).to_dict().items()}
    
    # Get data types
    dtypes = df.dtypes.astype(str).to_dict()
    
    # Count duplicates (convert to native Python int for JSON)
    duplicate_count = int(df.duplicated().sum())
    
    # Sample values (first non-null value for each column)
    sample_values = {}
    for col in df.columns:
        non_null = df[col].dropna()
        if len(non_null) > 0:
            sample_values[col] = str(non_null.iloc[0])[:50]  # Truncate long values
        else:
            sample_values[col] = None
    
    info = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "dtypes": dtypes,
        "missing_counts": missing_counts,
        "missing_percent": missing_percent,
        "duplicate_rows": duplicate_count,
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
        "sample_values": sample_values
    }
    
    return info


def print_csv_summary(df: pd.DataFrame) -> None:
    """
    Print a formatted summary of the DataFrame.
    
    Args:
        df: pandas DataFrame to summarize
    """
    info = get_csv_info(df)
    
    print("\n" + "=" * 60)
    print("CSV FILE SUMMARY")
    print("=" * 60)
    print(f"Rows: {info['rows']:,}")
    print(f"Columns: {info['columns']}")
    print(f"Memory Usage: {info['memory_usage_mb']} MB")
    print(f"Duplicate Rows: {info['duplicate_rows']:,}")
    
    print("\n" + "-" * 60)
    print("COLUMNS:")
    print("-" * 60)
    print(f"{'Column':<25} {'Type':<15} {'Missing':<10} {'Sample':<20}")
    print("-" * 60)
    
    for col in info['column_names']:
        dtype = info['dtypes'][col]
        missing = f"{info['missing_counts'][col]} ({info['missing_percent'][col]}%)"
        sample = str(info['sample_values'][col])[:20] if info['sample_values'][col] else "N/A"
        print(f"{str(col)[:24]:<25} {dtype:<15} {missing:<10} {sample}")
    
    print("=" * 60 + "\n")


# Example usage (for testing)
if __name__ == "__main__":
    # Test with a sample file
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            df = load_csv(filepath)
            is_valid, issues = validate_csv(df)
            if not is_valid:
                print("Validation issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            print_csv_summary(df)
        except Exception as e:
            print(f"Error: {e}")
