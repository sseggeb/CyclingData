# -*- coding: utf-8 -*-
"""
Created on Fri May  9 07:48:50 2025

@author: spencer
"""
import fitdecode
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
from datetime import timedelta
import os
import gzip
import plotly.graph_objects as go

def decompress_fit_gz(gz_file_path, output_directory=None):
    try:
        with gzip.open(gz_file_path, 'rb') as gz_file:
            file_content = gz_file.read()

        base_name, ext = os.path.splitext(gz_file_path)
        output_file_path = base_name #+ ".fit"

        if output_directory:
            os.makedirs(output_directory, exist_ok=True)
            output_file_path = os.path.join(output_directory, os.path.basename(output_file_path))

        with open(output_file_path, 'wb') as fit_file:
            fit_file.write(file_content)

        return output_file_path
    except Exception as e:
        print(f"Error decompressing {gz_file_path}: {e}")
        return None

def find_and_decompress_fit_files(root_directory, output_directory=None):
    """
    Recursively searches for .fit and .fit.gz files, decompresses the .fit.gz
    files, and returns a list of paths to all .fit files (original and decompressed).
    """
    fit_file_paths = []
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if filename.lower().endswith(".fit"):
                fit_file_paths.append(full_path)
            elif filename.lower().endswith(".fit.gz"):
                decompressed_path = decompress_fit_gz(full_path, output_directory)
                if decompressed_path:
                    fit_file_paths.append(decompressed_path)
    return fit_file_paths

def process_fit_files(file_paths):
    """
    Processes a list of .fit file paths, extracts the record data from each file, and returns a dictionary where keys are file paths and values are Pandas DataFrames.
    """
    all_data = {}
    for file_path in file_paths:
        record_data = []
        try:
            with open(file_path, 'rb') as fit_file:
                for frame in fitdecode.FitReader(fit_file):
                    if isinstance(frame, fitdecode.records.FitDataMessage):
                        if frame.name == 'record':
                            record = {}
                            for field in frame.fields:
                                record[field.name] = field.value
                            record_data.append(record)
        except fitdecode.exceptions.FitError as e:
            print(f"Error decoding .fit file: {file_path} - {e}")
            continue # move to the next file if there's an error
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            continue
        
        if record_data:
            df= pd.DataFrame(record_data)
            all_data[file_path] = df
        else:
            print(f"No 'record' data found in: {file_path}")
            
    return all_data

# Placeholder if all_workout_data is not readily available
root_directory = 'C:/Users/ssegg/OneDrive/Documents/data/cyclingdata2024' #directory where the .fit.gz files are located
decompressed_directory = 'C:/Users/ssegg/OneDrive/Documents/data/cyclingdata2024/decompressed' # directory for decompressed files to go to

all_fit_files = find_and_decompress_fit_files(root_directory, decompressed_directory)
if all_fit_files:
    all_workout_data = process_fit_files(all_fit_files)

    if all_workout_data:
        print("\nSuccessfully processed the .fit files. Here's a preview of the data from the first file:")
        first_file_path = list(all_workout_data.keys())[0]
        print(f"\nData from: {first_file_path}")
        print(all_workout_data[first_file_path].head())
        print("\n(The 'all_workout_data' dictionary now contains DataFrames for each processed file)")
        # Now you can iterate through the 'all_workout_data' dictionary to analyze each workout
        # For example:
        # for file_path, df in all_workout_data.items():
        #     print(f"\nAnalyzing data from: {file_path}")
        #     # Perform your analysis here (e.g., calculate mean power, plot heart rate)
    else:
        print("No workout data was extracted from the .fit files.")
else:
    print("No .fit or .fit.gz files found to process.")


if not all_workout_data:
    print("Warning: No workout data available. Please run your data processing steps first.")

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("TrainingPeaks .fit File Analyzer"),

    dcc.Dropdown(
        id='file-selector',
        options=[{'label': os.path.basename(f), 'value': f} for f in all_workout_data.keys()],
        placeholder="Select a .fit file"
    ),

    html.Div(id='output-summary'),
    
    # Add Graph components for time series plots
    html.Div([
        dcc.Graph(id='power-time-series'),
        dcc.Graph(id='heart-rate-time-series'),
        dcc.Graph(id='speed-time-series'),
        dcc.Graph(id='cadence-time-series')
        ])
])

def calculate_workout_summary(df):
    """(Same summary function as before)"""
    if df.empty:
        return "No data to summarize."

    summary = {}
    numerical_cols = df.select_dtypes(include=['number'])
    summary['basic_stats'] = numerical_cols.describe()

    if 'timestamp' in df.columns:
        summary['duration'] = (df['timestamp'].max() - df['timestamp'].min()) if not df['timestamp'].empty else timedelta(0)

    if 'power' in df.columns:
        summary['mean_power'] = df['power'].mean()
        summary['max_power'] = df['power'].max()

    if 'heart_rate' in df.columns:
        summary['mean_heart_rate'] = df['heart_rate'].mean()
        summary['max_heart_rate'] = df['heart_rate'].max()

    if 'speed' in df.columns:
        summary['mean_speed'] = df['speed'].mean()
        summary['max_speed'] = df['speed'].max()

    if 'cadence' in df.columns:
        summary['mean_cadence'] = df['cadence'].mean()
        summary['max_cadence'] = df['cadence'].max()

    if 'altitude' in df.columns:
        summary['min_altitude'] = df['altitude'].min()
        summary['max_altitude'] = df['altitude'].max()
        summary['altitude_gain'] = df['altitude'].max() - df['altitude'].min() if not df['altitude'].empty else None

    return summary

@app.callback(
    [Output('output-summary', 'children'),
     Output('power-time-series', 'figure'),
     Output('heart-rate-time-series','figure'),
     Output('speed-time-series', 'figure'),
     Output('cadence-time-series','figure')
     ],
    [Input('file-selector', 'value')]
)
def update_summary(selected_file):
    summary_output = html.P("Please select a .fit file to analyze.")
    power_figure = go.Figure() # Default empty figures
    heart_rate_figure = go.Figure()
    speed_figure = go.Figure()
    cadence_figure = go.Figure()
    
    
    if selected_file:
        if selected_file in all_workout_data:
            df = all_workout_data[selected_file]
            summary = calculate_workout_summary(df)
            
            # Update Summary Output
            output_components = [html.H3(f"Summary for: {os.path.basename(selected_file)}")]
            for key, value in summary.items():
                if isinstance(value, pd.DataFrame):
                    output_components.append(html.H4(key.replace('_', ' ').title()))
                    output_components.append(html.Pre(value.to_string()))
                else:
                    output_components.append(html.P(f"{key.replace('_', ' ').title()}: {value}"))
            summary_output = html.Div(output_components)
           
            # Create Time Series Plots
            if 'timestamp' in df.columns:
                if 'power' in df.columns:
                    power_figure = go.Figure(
                        data=[go.Scatter(x=df['timestamp'], y=df['power'], mode='lines')],
                        layout=go.Layout(
                            title='Power Over Time',
                            xaxis={'title': 'Time'},
                            yaxis={'title': 'Power (Watts)'}
                        )
                    )
                if 'heart_rate' in df.columns:
                    heart_rate_figure = go.Figure(
                        data=[go.Scatter(x=df['timestamp'], y=df['heart_rate'], mode='lines', marker={'color': 'red'})],
                        layout=go.Layout(
                            title='Heart Rate Over Time',
                            xaxis={'title': 'Time'},
                            yaxis={'title': 'Heart Rate (bpm)'}
                        )
                    )
                if 'speed' in df.columns:
                     # Convert speed if necessary (fitdecode often provides speed in m/s)
                     # Adjust this based on the actual unit in your .fit files
                     speed_figure = go.Figure(
                        data=[go.Scatter(x=df['timestamp'], y=df['speed'], mode='lines', marker={'color': 'green'})],
                        layout=go.Layout(
                            title='Speed Over Time',
                            xaxis={'title': 'Time'},
                            yaxis={'title': 'Speed'} # Add units here if known (e.g., m/s, km/h, mph)
                        )
                    )
                if 'cadence' in df.columns:
                    cadence_figure = go.Figure(
                        data=[go.Scatter(x=df['timestamp'], y=df['cadence'], mode='lines', marker={'color': 'purple'})],
                        layout=go.Layout(
                            title='Cadence Over Time',
                            xaxis={'title': 'Time'},
                            yaxis={'title': 'Cadence (rpm)'} # Adjust units if necessary
                        )
                    )
                # Create figures for other metrics similarly
            else:
                 summary_output = html.P(f"Error: 'timestamp' column not found in {os.path.basename(selected_file)}. Cannot plot time series.")


        else:
            summary_output = html.P("Error: Selected file not found in processed data.")

    # Return all outputs in the order defined in the @app.callback decorator
    return (summary_output, power_figure, heart_rate_figure, speed_figure, cadence_figure)

if __name__ == '__main__':
    app.run(port = 8000, debug=True)
    
# http://127.0.0.1:8000/