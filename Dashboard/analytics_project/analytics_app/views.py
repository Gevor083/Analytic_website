from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from .models import UploadedFile, ProcessedData
import pandas as pd
import json


def home(request):
    return render(request, 'analytics_app/home.html')


def upload_csv(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['csv_file']
        obj = UploadedFile.objects.create(file=uploaded_file)
        df = pd.read_csv(uploaded_file)

        numeric_columns = df.select_dtypes(include=['number']).columns
        chart_data = {}

        for col in numeric_columns:
            total = df[col].sum()
            ProcessedData.objects.create(uploaded_file=obj, column_name=col, value=total)
            chart_data[col] = df[col].tolist()  # Chart.js-ի համար

        # save chart data to session to pass to results page
        request.session['chart_data'] = json.dumps(chart_data)

        return redirect('results', file_id=obj.id)
    return render(request, 'analytics_app/upload.html')


def results(request, file_id):
    file_obj = UploadedFile.objects.get(id=file_id)
    data = ProcessedData.objects.filter(uploaded_file=file_obj)
    chart_data = json.loads(request.session.get('chart_data', '{}'))
    context = {'file': file_obj, 'data': data, 'chart_data': chart_data}
    return render(request, 'analytics_app/results.html', context)
