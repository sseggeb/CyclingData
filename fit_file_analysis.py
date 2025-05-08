# -*- coding: utf-8 -*-
"""
Created on Thu May  8 13:05:11 2025

@author: spencer
"""
import os
import fitdecode
import pandas as pd

def find_fit_files(root_directory):
    """
    """
    fit_file_paths = []
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.lower().endswith(".fit"):
                full_path = os.path.join(dirpath,filename)
                fit_file_paths.append(full_path)
    return

root_directory = 'C:/Users/spencer/OneDrive - R T Jones Capital Equities Inc/Desktop/Spencer/cyclingdata2020/'
fit_files = find_fit_files(root_directory)

if fit_files:
    print(f"Found {len(fit_files)} .fit files:")
    for file_path in fit_files:
        print(file_path)
else:
    print("No .fit files found in the specified directory or its subfolders.")

