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
all_workout_data = {}
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