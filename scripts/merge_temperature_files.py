#!/usr/bin/env python3
"""
Script to merge all temperature CSV files into one master file
"""

import pandas as pd
import glob
import os
from tqdm import tqdm

def merge_temperature_files():
    """
    Merge all temperature CSV files from data/temperature/ directory
    """
    print("Starting temperature file merge...")
    print("=" * 60)

    # Find all CSV files
    csv_files = glob.glob('data/temperature/*2025-2026_RR-T-Vent.csv')
    print(f"Found {len(csv_files)} CSV files to process")

    # Initialize empty list to store DataFrames
    dfs = []

    # Process each file
    for file_path in tqdm(csv_files, desc="Processing files"):
        try:
            # Read CSV with proper encoding and dtype
            df = pd.read_csv(
                file_path,
                sep=';',
                dtype={'NUM_POSTE': str},  # Keep station ID as string
                na_values=['', 'NA', 'N/A']
            )

            # Add source file column for reference
            df['SOURCE_FILE'] = os.path.basename(file_path)

            # Extract department from filename (Q_XX format)
            dept = os.path.basename(file_path).split('_')[1]
            df['DEPARTMENT'] = dept

            # Convert date from AAAAMMJJ to YYYY-MM-DD for sorting
            df['DATE'] = pd.to_datetime(df['AAAAMMJJ'], format='%Y%m%d')

            # Select only the requested columns (plus DATE for sorting)
            columns_to_keep = [
                'NUM_POSTE', 'NOM_USUEL', 'LAT', 'LON', 'ALTI',
                'AAAAMMJJ', 'RR', 'TN', 'TX', 'TM', 'TAMPLI', 'DATE'
            ]

            # Keep only columns that exist
            cols = [c for c in columns_to_keep if c in df.columns]
            df = df[cols]

            dfs.append(df)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    # Combine all DataFrames
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        print(f"\nCombined {len(combined_df)} records")

        # Sort by station and date
        combined_df = combined_df.sort_values(['NUM_POSTE', 'DATE'])

        # Remove DATE column before saving (not in requested fields)
        combined_df = combined_df.drop(columns=['DATE'])

        # Save to CSV
        output_file = 'temperature_2025_2026.csv'
        combined_df.to_csv(output_file, index=False, sep=';')
        print(f"\nSaved merged data to: {output_file}")
        print(f"File size: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")

        # Show summary
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print("=" * 60)
        print(f"Total records: {len(combined_df):,}")
        print(f"Unique stations: {combined_df['NUM_POSTE'].nunique()}")
        print(f"Date range: {combined_df['AAAAMMJJ'].min()} to {combined_df['AAAAMMJJ'].max()}")

        return combined_df
    else:
        print("No data to combine")
        return None

def analyze_temperature_data(df):
    """
    Perform basic analysis on temperature data
    """
    print("\n" + "=" * 60)
    print("TEMPERATURE ANALYSIS:")
    print("=" * 60)

    # Filter for days above 30°C
    hot_days = df[df['TX'] > 30]

    print(f"Total days with max temp > 30°C: {len(hot_days):,}")

    # Group by station
    station_stats = hot_days.groupby(['NUM_POSTE', 'NOM_USUEL', 'DEPARTMENT']).agg({
        'TX': ['count', 'mean', 'max'],
        'DATE': ['min', 'max']
    }).round(1)

    station_stats.columns = ['days_above_30', 'avg_temp', 'max_temp', 'first_date', 'last_date']
    station_stats = station_stats.sort_values('days_above_30', ascending=False)

    print("\nTop 10 stations with most hot days (>30°C):")
    print(station_stats.head(10).to_string())

    # Save hot days analysis
    station_stats.reset_index().to_csv('hot_days_analysis_2025_2026.csv', index=False, sep=';')
    print("\nSaved hot days analysis to: hot_days_analysis_2025_2026.csv")

if __name__ == '__main__':
    # Merge files
    merged_data = merge_temperature_files()

    # Analyze if data was merged
    if merged_data is not None:
        analyze_temperature_data(merged_data)

    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)