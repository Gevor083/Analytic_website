from celery import shared_task
import pandas as pd
import numpy as np
from .models import UploadedFile, ProcessedData
import json

@shared_task
def process_uploaded_file(file_id):
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        file_type = file_obj.file_type
        
        # Read file in chunks for large files
        chunk_size = 10000  # Adjust based on memory constraints
        
        if file_type == 'csv':
            df_iterator = pd.read_csv(file_obj.file.path, chunksize=chunk_size)
        elif file_type == 'json':
            df_iterator = pd.read_json(file_obj.file.path, lines=True, chunksize=chunk_size)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Initialize accumulators
        column_stats = {}
        
        # Process chunks
        for chunk_num, chunk in enumerate(df_iterator):
            for column in chunk.select_dtypes(include=[np.number]).columns:
                if column not in column_stats:
                    column_stats[column] = {
                        'sum': 0,
                        'count': 0,
                        'sum_sq': 0,  # For calculating std dev
                        'min': float('inf'),
                        'max': float('-inf'),
                        'missing': 0,
                        'values': []  # Keep limited sample for histogram
                    }
                
                stats = column_stats[column]
                series = chunk[column]
                non_null = series.dropna()
                
                stats['sum'] += non_null.sum()
                stats['count'] += len(non_null)
                stats['sum_sq'] += (non_null ** 2).sum()
                stats['min'] = min(stats['min'], non_null.min() if len(non_null) > 0 else stats['min'])
                stats['max'] = max(stats['max'], non_null.max() if len(non_null) > 0 else stats['max'])
                stats['missing'] += series.isna().sum()
                
                # Keep a sample of values for histogram (limit to 1000 values)
                if len(stats['values']) < 1000:
                    stats['values'].extend(non_null.sample(min(len(non_null), 1000 - len(stats['values']))).tolist())

        # Calculate final statistics and save
        for column, stats in column_stats.items():
            if stats['count'] > 0:
                mean = stats['sum'] / stats['count']
                variance = (stats['sum_sq'] / stats['count']) - (mean ** 2)
                std = np.sqrt(variance) if variance > 0 else 0
                
                # Calculate histogram
                hist, bins = np.histogram(stats['values'], bins=10)
                hist_data = {
                    'bins': bins.tolist(),
                    'counts': hist.tolist()
                }
                
                # Sanitize numeric types to native Python types before saving
                sanitized_stats = {
                    'mean': float(mean),
                    'std': float(std),
                    'min': float(stats['min']),
                    'max': float(stats['max']),
                    'count': int(stats['count']),
                    'missing': int(stats['missing']),
                    'histogram': {
                        'bins': [float(b) for b in bins.tolist()],
                        'counts': [int(h) for h in hist.tolist()]
                    }
                }

                # Save to database
                ProcessedData.objects.create(
                    uploaded_file=file_obj,
                    column_name=column,
                    value=float(mean),  # Store mean as the main value
                    stats=sanitized_stats
                )
        
        file_obj.processed = True
        file_obj.save()
        
    except Exception as e:
        file_obj.error_message = str(e)
        file_obj.save()
        raise