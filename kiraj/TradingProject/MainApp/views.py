from django import forms
from django.shortcuts import render
from io import TextIOWrapper
import csv
from datetime import datetime, timedelta
import json
from django.http import HttpResponse
class CandleForm(forms.Form):
    csv_file = forms.FileField()
    timeframe = forms.IntegerField(label='Timeframe (in minutes)')

def is_valid_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def parse_csv(file, timeframe):
    csv_data = []
    reader = csv.DictReader(TextIOWrapper(file, encoding='utf-8'))
    
    current_datetime = None
    current_candle = None
    aggregated_data = []
    
    for row in reader:
        date, time = row['DATE'], row['TIME']
        candle_datetime = datetime.strptime(f"{date} {time}", "%Y%m%d %H:%M")
        
        if current_datetime is None:
            current_datetime = candle_datetime
            current_candle = row
            current_candle['VOLUME'] = int(row['VOLUME']) if is_valid_integer(row['VOLUME']) else 0
        else:
            time_difference = candle_datetime - current_datetime
            if time_difference >= timedelta(minutes=timeframe):
                aggregated_data.append(current_candle)
                current_datetime = candle_datetime
                current_candle = row
                current_candle['VOLUME'] = int(row['VOLUME']) if is_valid_integer(row['VOLUME']) else 0
            else:
                current_candle['HIGH'] = max(float(current_candle['HIGH']), float(row['HIGH']))
                current_candle['LOW'] = min(float(current_candle['LOW']), float(row['LOW']))
                current_candle['CLOSE'] = float(row['CLOSE'])
                current_candle['VOLUME'] += int(row['VOLUME']) if is_valid_integer(row['VOLUME']) else 0
    
    return csv_data, aggregated_data

def upload_csv(request):
    csv_data = None
    aggregated_data = None
    if request.method == 'POST':
        form = CandleForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            timeframe = form.cleaned_data['timeframe']
            
            # Parse the uploaded CSV data with the specified timeframe
            csv_data, aggregated_data = parse_csv(csv_file, timeframe)
            
            # Convert aggregated_data to JSON
            aggregated_data_json = json.dumps(aggregated_data, ensure_ascii=False, indent=4)
            if aggregated_data_json:
                response = HttpResponse(aggregated_data_json, content_type='application/json')
                response['Content-Disposition'] = 'attachment; filename="aggregated_data.json"'
        return response
    else:
        form = CandleForm()
        aggregated_data_json = None
    
    return render(request, 'upload.html', {'form': form, 'csv_data': csv_data, 'aggregated_data': aggregated_data, 'aggregated_data_json': aggregated_data_json})
