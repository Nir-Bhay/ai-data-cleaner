"""
Database Manager Module
-----------------------
Handles SQLite database operations for storing cleaned data and metadata.
"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """
    Get a database connection.
    
    Returns:
        SQLite connection object
    """
    # Ensure database directory exists
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn


def init_database() -> None:
    """
    Initialize the database with required tables.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create cleaned_datasets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cleaned_datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT UNIQUE NOT NULL,
            original_filename TEXT NOT NULL,
            rows_count INTEGER,
            columns_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create cleaning_metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cleaning_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER NOT NULL,
            user_prompt TEXT,
            applied_rules TEXT,
            parser_used TEXT,
            rows_before INTEGER,
            rows_after INTEGER,
            actions_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES cleaned_datasets(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✓ Database initialized")


def generate_table_name(original_filename: str) -> str:
    """
    Generate a unique table name from the original filename.
    
    Args:
        original_filename: Original CSV filename
        
    Returns:
        Unique table name
    """
    import re
    from datetime import datetime
    
    # Clean the filename
    base_name = Path(original_filename).stem
    clean_name = re.sub(r'[^\w]', '_', base_name.lower())
    clean_name = re.sub(r'_+', '_', clean_name).strip('_')
    
    # Add timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"data_{clean_name}_{timestamp}"


def save_dataset(
    df: pd.DataFrame,
    original_filename: str,
    user_prompt: str,
    rules: List[Dict[str, Any]],
    parser_used: str,
    rows_before: int,
    actions_log: List[str]
) -> int:
    """
    Save a cleaned dataset to the database.
    
    Args:
        df: Cleaned pandas DataFrame
        original_filename: Original CSV filename
        user_prompt: User's cleaning instructions
        rules: Applied cleaning rules
        parser_used: Which parser was used (gemini or pattern)
        rows_before: Row count before cleaning
        actions_log: List of actions applied
        
    Returns:
        Dataset ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Generate table name
    table_name = generate_table_name(original_filename)
    
    try:
        # Save the DataFrame to its own table
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # Record in cleaned_datasets
        cursor.execute("""
            INSERT INTO cleaned_datasets (table_name, original_filename, rows_count, columns_count)
            VALUES (?, ?, ?, ?)
        """, (table_name, original_filename, len(df), len(df.columns)))
        
        dataset_id = cursor.lastrowid
        
        # Record metadata
        cursor.execute("""
            INSERT INTO cleaning_metadata 
            (dataset_id, user_prompt, applied_rules, parser_used, rows_before, rows_after, actions_log)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            dataset_id,
            user_prompt,
            json.dumps(rules),
            parser_used,
            rows_before,
            len(df),
            json.dumps(actions_log)
        ))
        
        conn.commit()
        print(f"✓ Dataset saved to table: {table_name}")
        print(f"✓ Dataset ID: {dataset_id}")
        
        return dataset_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_dataset(dataset_id: int) -> Optional[pd.DataFrame]:
    """
    Retrieve a cleaned dataset by ID.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        pandas DataFrame or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get table name
    cursor.execute("""
        SELECT table_name FROM cleaned_datasets WHERE id = ?
    """, (dataset_id,))
    
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return None
    
    table_name = result['table_name']
    
    # Load DataFrame from table
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    
    return df


def get_dataset_by_table_name(table_name: str) -> Optional[pd.DataFrame]:
    """
    Retrieve a dataset by table name.
    
    Args:
        table_name: Database table name
        
    Returns:
        pandas DataFrame or None if not found
    """
    conn = get_connection()
    
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        return df
    except Exception:
        return None
    finally:
        conn.close()


def list_datasets() -> List[Dict[str, Any]]:
    """
    List all saved datasets.
    
    Returns:
        List of dataset records
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            cd.id,
            cd.table_name,
            cd.original_filename,
            cd.rows_count,
            cd.columns_count,
            cd.created_at,
            cm.user_prompt,
            cm.parser_used,
            cm.rows_before
        FROM cleaned_datasets cd
        LEFT JOIN cleaning_metadata cm ON cd.id = cm.dataset_id
        ORDER BY cd.created_at DESC
    """)
    
    results = []
    for row in cursor.fetchall():
        results.append(dict(row))
    
    conn.close()
    return results


def get_metadata(dataset_id: int) -> Optional[Dict[str, Any]]:
    """
    Get full metadata for a dataset.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        Metadata dictionary or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            cd.*,
            cm.user_prompt,
            cm.applied_rules,
            cm.parser_used,
            cm.rows_before,
            cm.rows_after,
            cm.actions_log,
            cm.created_at as cleaning_timestamp
        FROM cleaned_datasets cd
        LEFT JOIN cleaning_metadata cm ON cd.id = cm.dataset_id
        WHERE cd.id = ?
    """, (dataset_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        metadata = dict(result)
        # Parse JSON fields
        if metadata.get('applied_rules'):
            metadata['applied_rules'] = json.loads(metadata['applied_rules'])
        if metadata.get('actions_log'):
            metadata['actions_log'] = json.loads(metadata['actions_log'])
        return metadata
    
    return None


def export_for_powerbi(dataset_id: int, output_path: str) -> str:
    """
    Export a dataset as Power BI compatible CSV.
    
    Args:
        dataset_id: Dataset ID
        output_path: Output file path
        
    Returns:
        Path to the exported file
    """
    df = get_dataset(dataset_id)
    
    if df is None:
        raise ValueError(f"Dataset with ID {dataset_id} not found")
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Export with UTF-8 BOM for Power BI compatibility
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"✓ Exported to: {output_file}")
    return str(output_file)


def delete_dataset(dataset_id: int) -> bool:
    """
    Delete a dataset and its metadata.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        True if deleted, False if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get table name first
    cursor.execute("SELECT table_name FROM cleaned_datasets WHERE id = ?", (dataset_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
    
    table_name = result['table_name']
    
    try:
        # Drop the data table
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Delete metadata
        cursor.execute("DELETE FROM cleaning_metadata WHERE dataset_id = ?", (dataset_id,))
        
        # Delete dataset record
        cursor.execute("DELETE FROM cleaned_datasets WHERE id = ?", (dataset_id,))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# Initialize database on module import
init_database()


# Example usage
if __name__ == "__main__":
    # Test database operations
    print("Testing Database Manager")
    print("=" * 50)
    
    # List existing datasets
    datasets = list_datasets()
    print(f"\nExisting datasets: {len(datasets)}")
    for ds in datasets:
        print(f"  - ID: {ds['id']}, File: {ds['original_filename']}, Rows: {ds['rows_count']}")
