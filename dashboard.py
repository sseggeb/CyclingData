# -*- coding: utf-8 -*-
"""
Created on Fri May  9 07:48:50 2025

@author: spencer
"""

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
from datetime import timedelta
import os

# Placeholder if all_workout_data is not readily available
root_directory = 'C:/Users/spencer/Documents/cyclingdata2020' #directory where the .fit.gz files are located
decompressed_directory = 'C:/Users/spencer/Documents/cyclingdata2020/decompressed' # directory for decompressed files to go to

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

    html.Div(id='output-summary')
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
    Output('output-summary', 'children'),
    [Input('file-selector', 'value')]
)
def update_summary(selected_file):
    if selected_file:
        if selected_file in all_workout_data:
            df = all_workout_data[selected_file]
            summary = calculate_workout_summary(df)
            output_components = [html.H3(f"Summary for: {os.path.basename(selected_file)}")]
            for key, value in summary.items():
                if isinstance(value, pd.DataFrame):
                    output_components.append(html.H4(key.replace('_', ' ').title()))
                    output_components.append(html.Div(value.to_string().replace('\n', html.Br().__str__())))
                else:
                    output_components.append(html.P(f"{key.replace('_', ' ').title()}: {value}"))
            return html.Div(output_components)
        else:
            return html.P("Error: Selected file not found in processed data.")
    else:
        return html.P("Please select a .fit file to analyze.")

if __name__ == '__main__':
    app.run(debug=True)