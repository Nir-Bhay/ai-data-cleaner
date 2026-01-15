"""
AI-Assisted Data Cleaning System - Web Application
===================================================
Flask-based web interface for cleaning CSV data using natural language.
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.csv_loader import load_csv, validate_csv, get_csv_info
from modules.rule_parser import parse_rules
from modules.data_cleaner import clean_data
from modules.db_manager import (
    init_database, save_dataset, get_dataset, list_datasets,
    get_metadata, export_for_powerbi, delete_dataset
)
from config import UPLOADS_DIR, EXPORTS_DIR

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['UPLOAD_FOLDER'] = str(UPLOADS_DIR)

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# WEB PAGES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle CSV file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files are allowed'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_filename = f"{timestamp}_{filename}"
        filepath = UPLOADS_DIR / saved_filename
        file.save(str(filepath))
        
        # Load and analyze
        df = load_csv(str(filepath))
        is_valid, issues = validate_csv(df)
        info = get_csv_info(df)
        
        # Get preview data (first 10 rows) - replace NaN with None for JSON
        preview = df.head(10).fillna('').to_dict('records')
        
        return jsonify({
            'success': True,
            'filename': saved_filename,
            'original_name': filename,
            'info': {
                'rows': info['rows'],
                'columns': info['columns'],
                'column_names': info['column_names'],
                'dtypes': info['dtypes'],
                'missing_counts': info['missing_counts'],
                'missing_percent': info['missing_percent'],
                'duplicate_rows': info['duplicate_rows']
            },
            'preview': preview,
            'validation': {
                'is_valid': is_valid,
                'issues': issues
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/clean', methods=['POST'])
def clean_file():
    """Clean the uploaded CSV file based on prompt."""
    data = request.json
    
    if not data or 'filename' not in data or 'prompt' not in data:
        return jsonify({'error': 'Missing filename or prompt'}), 400
    
    filename = data['filename']
    prompt = data['prompt']
    
    try:
        # Load file
        filepath = UPLOADS_DIR / filename
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404
        
        df = load_csv(str(filepath))
        rows_before = len(df)
        columns = df.columns.tolist()
        
        # Parse rules
        rules_result = parse_rules(prompt, columns)
        
        if not rules_result['rules']:
            return jsonify({
                'error': 'No cleaning rules detected from your prompt. Try being more specific.',
                'suggestions': [
                    'Remove duplicate rows',
                    'Fill missing values with mean',
                    'Remove rows where age < 18',
                    'Standardize column names'
                ]
            }), 400
        
        # Apply cleaning
        cleaned_df, actions_log = clean_data(df.copy(), rules_result['rules'])
        rows_after = len(cleaned_df)
        
        # Save to database
        dataset_id = save_dataset(
            df=cleaned_df,
            original_filename=filename,
            user_prompt=prompt,
            rules=rules_result['rules'],
            parser_used=rules_result['parser_used'],
            rows_before=rows_before,
            actions_log=actions_log
        )
        
        # Get preview of cleaned data - replace NaN for JSON
        preview = cleaned_df.head(10).fillna('').to_dict('records')
        
        return jsonify({
            'success': True,
            'dataset_id': dataset_id,
            'parser_used': rules_result['parser_used'],
            'rules_applied': rules_result['rules'],
            'actions_log': actions_log,
            'stats': {
                'rows_before': rows_before,
                'rows_after': rows_after,
                'rows_removed': rows_before - rows_after,
                'columns': len(cleaned_df.columns)
            },
            'preview': preview,
            'column_names': cleaned_df.columns.tolist()
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get cleaning history."""
    try:
        datasets = list_datasets()
        return jsonify({
            'success': True,
            'datasets': datasets
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dataset/<int:dataset_id>', methods=['GET'])
def get_dataset_details(dataset_id):
    """Get details of a specific dataset."""
    try:
        metadata = get_metadata(dataset_id)
        
        if not metadata:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Get the data
        df = get_dataset(dataset_id)
        preview = df.head(20).to_dict('records') if df is not None else []
        
        return jsonify({
            'success': True,
            'metadata': metadata,
            'preview': preview,
            'columns': df.columns.tolist() if df is not None else []
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/<int:dataset_id>', methods=['GET'])
def export_dataset(dataset_id):
    """Export dataset as CSV or Excel for Power BI."""
    try:
        metadata = get_metadata(dataset_id)
        if not metadata:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Check format parameter
        export_format = request.args.get('format', 'csv').lower()
        
        if export_format == 'excel':
            # Export as Excel
            export_filename = f"cleaned_dataset_{dataset_id}.xlsx"
            export_path = EXPORTS_DIR / export_filename
            
            # Get the dataset
            df = get_dataset(dataset_id)
            if df is None:
                return jsonify({'error': 'Dataset data not found'}), 404
            
            # Save as Excel with xlsxwriter for better compatibility
            df.to_excel(str(export_path), index=False, engine='openpyxl')
            
            return send_file(
                str(export_path),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=export_filename
            )
        else:
            # Export as CSV (default)
            export_filename = f"cleaned_dataset_{dataset_id}.csv"
            export_path = EXPORTS_DIR / export_filename
            exported_file = export_for_powerbi(dataset_id, str(export_path))
            
            return send_file(
                exported_file,
                mimetype='text/csv',
                as_attachment=True,
                download_name=export_filename
            )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete/<int:dataset_id>', methods=['DELETE'])
def delete_dataset_api(dataset_id):
    """Delete a dataset."""
    try:
        if delete_dataset(dataset_id):
            return jsonify({'success': True, 'message': f'Dataset {dataset_id} deleted'})
        else:
            return jsonify({'error': 'Dataset not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get prompt suggestions based on common cleaning tasks."""
    suggestions = [
        {"text": "Remove duplicate rows", "category": "Duplicates"},
        {"text": "Fill missing values with mean", "category": "Missing Values"},
        {"text": "Fill missing values with median", "category": "Missing Values"},
        {"text": "Drop rows with missing values", "category": "Missing Values"},
        {"text": "Standardize column names", "category": "Formatting"},
        {"text": "Convert date column to datetime", "category": "Data Types"},
        {"text": "Remove rows where age < 18", "category": "Filtering"},
        {"text": "Remove rows where status = inactive", "category": "Filtering"},
    ]
    return jsonify({'suggestions': suggestions})


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 AI-Assisted Data Cleaning System")
    print("=" * 60)
    print(f"📁 Uploads: {UPLOADS_DIR}")
    print(f"📤 Exports: {EXPORTS_DIR}")
    print("-" * 60)
    print("🌐 Open in browser: http://localhost:5000")
    print("=" * 60 + "\n")
    
    # Initialize database
    init_database()
    
    # Run server
    app.run(debug=True, host='0.0.0.0', port=5000)
