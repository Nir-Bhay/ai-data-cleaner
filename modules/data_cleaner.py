"""
Data Cleaner Module
-------------------
Executes data cleaning operations using Pandas.
"""
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


def clean_data(df: pd.DataFrame, rules: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Apply a list of cleaning rules to a DataFrame.
    
    Args:
        df: pandas DataFrame to clean
        rules: List of rule dictionaries
        
    Returns:
        Tuple of (cleaned DataFrame, list of applied actions)
    """
    actions_applied = []
    
    for rule in rules:
        action = rule.get("action")
        params = rule.get("params", {})
        
        print(f"  Applying: {action}...")
        
        try:
            if action == "remove_duplicates":
                df, msg = remove_duplicates(df, params)
            elif action == "fill_missing":
                df, msg = fill_missing(df, params)
            elif action == "standardize_columns":
                df, msg = standardize_columns(df)
            elif action == "filter_rows":
                df, msg = filter_rows(df, params)
            elif action == "convert_dtype":
                df, msg = convert_dtype(df, params)
            elif action == "drop_columns":
                df, msg = drop_columns(df, params)
            elif action == "rename_columns":
                df, msg = rename_columns(df, params)
            else:
                msg = f"Unknown action: {action}"
                print(f"    ⚠ {msg}")
                continue
            
            actions_applied.append(msg)
            print(f"    ✓ {msg}")
            
        except Exception as e:
            error_msg = f"Error in {action}: {str(e)}"
            actions_applied.append(error_msg)
            print(f"    ✗ {error_msg}")
    
    return df, actions_applied


def remove_duplicates(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
    """
    Remove duplicate rows from DataFrame.
    
    Args:
        df: pandas DataFrame
        params: {"columns": "all" or list of column names}
        
    Returns:
        Tuple of (cleaned DataFrame, action message)
    """
    before_count = len(df)
    
    columns = params.get("columns", "all")
    
    if columns == "all" or columns is None:
        df = df.drop_duplicates()
    else:
        # Ensure columns is a list
        if isinstance(columns, str):
            columns = [columns]
        # Only use columns that exist
        valid_cols = [c for c in columns if c in df.columns]
        if valid_cols:
            df = df.drop_duplicates(subset=valid_cols)
    
    after_count = len(df)
    removed = before_count - after_count
    
    return df, f"Removed {removed} duplicate rows"


def fill_missing(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
    """
    Fill or drop missing values.
    
    Args:
        df: pandas DataFrame
        params: {
            "columns": "all" or list of column names,
            "method": "mean" | "median" | "mode" | "drop" | "value" | "ffill" | "bfill",
            "value": value to fill with (if method is "value")
        }
        
    Returns:
        Tuple of (cleaned DataFrame, action message)
    """
    columns = params.get("columns", "all")
    method = params.get("method", "drop")
    fill_value = params.get("value")
    
    # Determine which columns to process
    if columns == "all" or columns is None:
        target_cols = df.columns.tolist()
    else:
        if isinstance(columns, str):
            columns = [columns]
        target_cols = [c for c in columns if c in df.columns]
    
    before_missing = df[target_cols].isna().sum().sum()
    
    if method == "drop":
        # Drop rows with missing values in target columns
        df = df.dropna(subset=target_cols)
        msg = f"Dropped rows with missing values in {len(target_cols)} columns"
        
    elif method == "mean":
        for col in target_cols:
            if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                df[col] = df[col].fillna(df[col].mean())
        msg = f"Filled missing with mean in numeric columns"
        
    elif method == "median":
        for col in target_cols:
            if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                df[col] = df[col].fillna(df[col].median())
        msg = f"Filled missing with median in numeric columns"
        
    elif method == "mode":
        for col in target_cols:
            mode_val = df[col].mode()
            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val.iloc[0])
        msg = f"Filled missing with mode"
        
    elif method == "value":
        if fill_value is not None:
            for col in target_cols:
                df[col] = df[col].fillna(fill_value)
            msg = f"Filled missing with value: {fill_value}"
        else:
            msg = "No fill value provided"
            
    elif method == "ffill":
        df[target_cols] = df[target_cols].ffill()
        msg = "Forward filled missing values"
        
    elif method == "bfill":
        df[target_cols] = df[target_cols].bfill()
        msg = "Backward filled missing values"
        
    else:
        msg = f"Unknown fill method: {method}"
    
    after_missing = df[target_cols].isna().sum().sum() if len(df) > 0 else 0
    filled = before_missing - after_missing
    
    return df, f"{msg} ({filled} values affected)"


def standardize_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """
    Standardize column names to lowercase with underscores.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        Tuple of (cleaned DataFrame, action message)
    """
    original_names = df.columns.tolist()
    
    # Create new names
    new_names = []
    for col in original_names:
        # Convert to string and lowercase
        new_name = str(col).lower()
        # Replace spaces and special chars with underscores
        new_name = re.sub(r'[^\w\s]', '', new_name)
        new_name = re.sub(r'\s+', '_', new_name)
        new_name = re.sub(r'_+', '_', new_name)  # Remove multiple underscores
        new_name = new_name.strip('_')
        new_names.append(new_name)
    
    # Handle duplicate names
    seen = {}
    final_names = []
    for name in new_names:
        if name in seen:
            seen[name] += 1
            final_names.append(f"{name}_{seen[name]}")
        else:
            seen[name] = 0
            final_names.append(name)
    
    df.columns = final_names
    
    # Count how many changed
    changed = sum(1 for o, n in zip(original_names, final_names) if o != n)
    
    return df, f"Standardized {changed} column names"


def filter_rows(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
    """
    Filter rows based on a condition.
    
    Args:
        df: pandas DataFrame
        params: {"condition": "pandas query string"}
        
    Returns:
        Tuple of (filtered DataFrame, action message)
    """
    condition = params.get("condition", "")
    
    if not condition:
        return df, "No filter condition provided"
    
    before_count = len(df)
    
    try:
        # Try using pandas query
        df = df.query(condition)
    except Exception:
        # Fallback: try eval with dataframe
        try:
            mask = eval(f"df['{condition.split()[0]}'] {' '.join(condition.split()[1:])}")
            df = df[mask]
        except Exception as e:
            return df, f"Could not apply filter: {condition}"
    
    after_count = len(df)
    removed = before_count - after_count
    
    return df, f"Filtered rows with condition '{condition}' (removed {removed} rows)"


def convert_dtype(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
    """
    Convert column data type.
    
    Args:
        df: pandas DataFrame
        params: {"column": "column_name", "dtype": "int|float|str|datetime|bool"}
        
    Returns:
        Tuple of (cleaned DataFrame, action message)
    """
    column = params.get("column")
    dtype = params.get("dtype")
    
    if not column or column not in df.columns:
        return df, f"Column '{column}' not found"
    
    if not dtype:
        return df, "No target dtype specified"
    
    original_dtype = str(df[column].dtype)
    
    try:
        if dtype in ["int", "integer"]:
            # Handle NaN before converting to int
            df[column] = pd.to_numeric(df[column], errors='coerce')
            if df[column].isna().any():
                df[column] = df[column].fillna(0)
            df[column] = df[column].astype(int)
            
        elif dtype in ["float", "decimal", "number"]:
            df[column] = pd.to_numeric(df[column], errors='coerce')
            
        elif dtype in ["str", "string", "text"]:
            df[column] = df[column].astype(str)
            
        elif dtype in ["date", "datetime"]:
            df[column] = pd.to_datetime(df[column], errors='coerce')
            
        elif dtype in ["bool", "boolean"]:
            # Handle various boolean representations
            true_vals = ['true', 'yes', '1', 'y', 't']
            df[column] = df[column].astype(str).str.lower().isin(true_vals)
            
        else:
            return df, f"Unknown dtype: {dtype}"
            
    except Exception as e:
        return df, f"Could not convert {column}: {str(e)}"
    
    return df, f"Converted '{column}' from {original_dtype} to {dtype}"


def drop_columns(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
    """
    Drop specified columns from DataFrame.
    
    Args:
        df: pandas DataFrame
        params: {"columns": list of column names}
        
    Returns:
        Tuple of (cleaned DataFrame, action message)
    """
    columns = params.get("columns", [])
    
    if isinstance(columns, str):
        columns = [columns]
    
    # Only drop columns that exist
    valid_cols = [c for c in columns if c in df.columns]
    
    if not valid_cols:
        return df, "No valid columns to drop"
    
    df = df.drop(columns=valid_cols)
    
    return df, f"Dropped {len(valid_cols)} columns: {valid_cols}"


def rename_columns(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
    """
    Rename columns in DataFrame.
    
    Args:
        df: pandas DataFrame
        params: {"mapping": {"old_name": "new_name", ...}}
        
    Returns:
        Tuple of (cleaned DataFrame, action message)
    """
    mapping = params.get("mapping", {})
    
    if not mapping:
        return df, "No column mapping provided"
    
    # Only rename columns that exist
    valid_mapping = {k: v for k, v in mapping.items() if k in df.columns}
    
    if not valid_mapping:
        return df, "No valid columns to rename"
    
    df = df.rename(columns=valid_mapping)
    
    return df, f"Renamed {len(valid_mapping)} columns"


# Example usage
if __name__ == "__main__":
    # Create sample data
    data = {
        "Name": ["Alice", "Bob", "Charlie", "Alice", None],
        "Age": [25, 30, None, 25, 22],
        "Email": ["alice@test.com", "bob@test.com", "charlie@test.com", "alice@test.com", "dave@test.com"],
        "Join Date": ["2023-01-15", "2023-02-20", "2023-03-10", "2023-01-15", "2023-04-05"]
    }
    df = pd.DataFrame(data)
    
    print("Original DataFrame:")
    print(df)
    print()
    
    # Test rules
    rules = [
        {"action": "remove_duplicates", "params": {"columns": "all"}},
        {"action": "fill_missing", "params": {"columns": ["Age"], "method": "mean"}},
        {"action": "standardize_columns", "params": {}},
        {"action": "convert_dtype", "params": {"column": "join_date", "dtype": "datetime"}}
    ]
    
    print("\nApplying cleaning rules...")
    print("=" * 50)
    
    cleaned_df, actions = clean_data(df, rules)
    
    print("\n" + "=" * 50)
    print("\nCleaned DataFrame:")
    print(cleaned_df)
    print(f"\nData types:\n{cleaned_df.dtypes}")
