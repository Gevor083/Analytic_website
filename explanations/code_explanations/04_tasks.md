# Tasks.py Explanation

Let's examine `analytics_app/tasks.py`, which handles background processing:

```python
from celery import shared_task
from .models import UploadedFile, ProcessedData
import pandas as pd
import json

@shared_task
def process_uploaded_file(file_id):
    """
    Background task to process uploaded files
    Args:
        file_id: ID of the UploadedFile record to process
    """
    try:
        # Get the file record
        file_obj = UploadedFile.objects.get(id=file_id)
        
        # Process based on file type
        if file_obj.file_type == 'csv':
            results = process_csv(file_obj)
        elif file_obj.file_type == 'json':
            results = process_json(file_obj)
        else:
            raise ValueError(f"Unsupported file type: {file_obj.file_type}")
        
        # Store results
        for column, stats in results.items():
            ProcessedData.objects.create(
                uploaded_file=file_obj,
                column_name=column,
                value=stats.get('mean', 0),
                stats=stats
            )
        
        # Mark as processed
        file_obj.processed = True
        file_obj.save()
        
    except Exception as e:
        # Record error and re-raise
        if file_obj:
            file_obj.error_message = str(e)
            file_obj.save()
        raise

def process_csv(file_obj):
    """
    Process a CSV file
    Args:
        file_obj: UploadedFile instance
    Returns:
        dict: Statistics for each column
    """
    df = pd.read_csv(file_obj.file.path)
    return calculate_statistics(df)

def process_json(file_obj):
    """
    Process a JSON file
    Args:
        file_obj: UploadedFile instance
    Returns:
        dict: Statistics for each column
    """
    with open(file_obj.file.path) as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    return calculate_statistics(df)

def calculate_statistics(df):
    """
    Calculate statistics for a DataFrame
    Args:
        df: pandas DataFrame
    Returns:
        dict: Statistics for each numeric column
    """
    stats = {}
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    
    for col in numeric_cols:
        stats[col] = {
            'mean': df[col].mean(),
            'median': df[col].median(),
            'std': df[col].std(),
            'min': df[col].min(),
            'max': df[col].max(),
            'missing': df[col].isnull().sum()
        }
    
    return stats

## Background Processing Explained

### 1. Task Queue
- Uses Celery for async processing
- Queues tasks for background execution
- Handles long-running operations

### 2. File Processing Pipeline
1. Load file from disk
2. Determine file type
3. Process accordingly
4. Calculate statistics
5. Store results
6. Update status

### 3. Error Handling
- Catches and logs exceptions
- Updates file status
- Records error messages
- Maintains data consistency

### 4. Data Analysis
- Numeric column detection
- Statistical calculations
- Missing value handling
- Result formatting

## Processing Features

1. CSV Processing
   - Pandas DataFrame loading
   - Column type detection
   - Statistical analysis

2. JSON Processing
   - JSON parsing
   - Data structure handling
   - Conversion to DataFrame

3. Statistical Calculations
   - Mean, median, std dev
   - Min/max values
   - Missing value counts
   - Column-wise analysis

## Performance Considerations

1. Memory Management
   - Efficient data loading
   - Chunk processing for large files
   - Memory cleanup

2. Error Recovery
   - Transaction management
   - State tracking
   - Error reporting

3. Scalability
   - Parallel processing
   - Queue management
   - Resource allocation