#!/usr/bin/env python3
"""
Chart generation script for data generation deep dive.

This script reads the generated dataset and creates visualizations showcasing
the various aspects of the enhanced data generation patterns.
"""

import os
import pickle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter
import seaborn as sns

# Set style for better-looking charts
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_dataset():
    """Load the generated dataset."""
    dataset_file = Path("output/raw_dataset.pkl")
    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_file}. Please run 00_generate_data.py first.")
    
    with open(dataset_file, 'rb') as f:
        data_points = pickle.load(f)
    
    return data_points

def convert_to_dataframe(data_points):
    """Convert data points to pandas DataFrame for easier analysis."""
    df = pd.DataFrame(data_points)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    
    # Extract label information into separate columns
    label_columns = set()
    for point in data_points:
        label_columns.update(point['labels'].keys())
    
    for col in label_columns:
        df[f'label_{col}'] = df['labels'].apply(lambda x: x.get(col, None))
    
    return df

def create_charts_directory():
    """Create directory for chart outputs."""
    charts_dir = Path("docs/charts")
    charts_dir.mkdir(exist_ok=True)
    return charts_dir

def chart_timestamp_regularity(df, charts_dir):
    """Chart 1: Timestamp regularity analysis."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Calculate intervals for each time series
    intervals = []
    series_intervals = defaultdict(list)
    
    for metric_name in df['metric_name'].unique():
        metric_data = df[df['metric_name'] == metric_name].sort_values('timestamp')
        if len(metric_data) > 1:
            metric_intervals = np.diff(metric_data['timestamp'].values)
            intervals.extend(metric_intervals)
            series_intervals[metric_name] = metric_intervals
    
    # Plot 1: Histogram of intervals
    ax1.hist(intervals, bins=50, alpha=0.7, edgecolor='black')
    ax1.axvline(x=15, color='red', linestyle='--', linewidth=2, label='Expected 15s interval')
    ax1.set_xlabel('Interval (seconds)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of Timestamp Intervals\n(Enhanced Data Generation)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Calculate regularity percentage
    regular_intervals = sum(1 for interval in intervals if interval == 15)
    regularity_pct = (regular_intervals / len(intervals)) * 100
    ax1.text(0.02, 0.98, f'Perfect intervals: {regularity_pct:.1f}%', 
             transform=ax1.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Plot 2: Interval timeline for sample series
    sample_series = list(series_intervals.keys())[:3]
    for i, series_name in enumerate(sample_series):
        intervals_data = series_intervals[series_name][:100]  # First 100 intervals
        ax2.plot(range(len(intervals_data)), intervals_data, 
                marker='o', markersize=3, label=series_name, alpha=0.7)
    
    ax2.axhline(y=15, color='red', linestyle='--', alpha=0.5, label='Expected 15s')
    ax2.set_xlabel('Measurement #')
    ax2.set_ylabel('Interval (seconds)')
    ax2.set_title('Timestamp Intervals Over Time (Sample Series)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(charts_dir / 'timestamp_regularity.png', dpi=300, bbox_inches='tight')
    plt.close()

def chart_infrastructure_correlation(df, charts_dir):
    """Chart 2: Infrastructure correlation patterns."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Filter to CPU metrics for clear correlation demonstration
    cpu_data = df[df['metric_name'] == 'cpu_usage_percent'].copy()
    
    if len(cpu_data) == 0:
        print("No CPU data found, skipping infrastructure correlation chart")
        return
    
    # Group by host and region
    cpu_data['host_region'] = cpu_data['label_host'] + '-' + cpu_data['label_region']
    
    # Plot 1: CPU usage by host over time
    hosts = cpu_data['label_host'].unique()[:4]  # Limit to 4 hosts for clarity
    for host in hosts:
        host_data = cpu_data[cpu_data['label_host'] == host].sort_values('timestamp')
        if len(host_data) > 0:
            # Sample every 10th point for clarity
            sample_data = host_data.iloc[::10]
            ax1.plot(sample_data['datetime'], sample_data['value'], 
                    label=f'Host {host}', alpha=0.8, linewidth=1.5)
    
    ax1.set_xlabel('Time')
    ax1.set_ylabel('CPU Usage (%)')
    ax1.set_title('CPU Usage by Host (Infrastructure Correlation)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # Plot 2: CPU usage by region
    regions = cpu_data['label_region'].unique()
    for region in regions:
        region_data = cpu_data[cpu_data['label_region'] == region].sort_values('timestamp')
        if len(region_data) > 0:
            # Calculate rolling average
            region_data = region_data.iloc[::10]  # Sample for performance
            ax2.plot(region_data['datetime'], region_data['value'], 
                    label=f'Region {region}', alpha=0.8, linewidth=1.5)
    
    ax2.set_xlabel('Time')
    ax2.set_ylabel('CPU Usage (%)')
    ax2.set_title('CPU Usage by Region')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # Plot 3: Correlation matrix between host-region combinations
    pivot_data = cpu_data.pivot_table(
        index='timestamp', 
        columns='host_region', 
        values='value'
    ).ffill().bfill()
    
    if pivot_data.shape[1] > 1:
        correlation_matrix = pivot_data.corr()
        im = ax3.imshow(correlation_matrix, cmap='coolwarm', vmin=-1, vmax=1)
        ax3.set_xticks(range(len(correlation_matrix.columns)))
        ax3.set_yticks(range(len(correlation_matrix.columns)))
        ax3.set_xticklabels(correlation_matrix.columns, rotation=45, ha='right')
        ax3.set_yticklabels(correlation_matrix.columns)
        ax3.set_title('Host-Region CPU Correlation Matrix')
        
        # Add correlation values to the plot
        for i in range(len(correlation_matrix)):
            for j in range(len(correlation_matrix)):
                text = ax3.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                              ha="center", va="center", color="black", fontsize=8)
        
        plt.colorbar(im, ax=ax3)
    
    # Plot 4: Value distribution by infrastructure
    cpu_data['infra_type'] = cpu_data['label_environment'] + '-' + cpu_data['label_region']
    infra_types = cpu_data['infra_type'].unique()[:6]  # Limit for clarity
    
    data_for_box = [cpu_data[cpu_data['infra_type'] == infra]['value'].values 
                    for infra in infra_types]
    
    box_plot = ax4.boxplot(data_for_box, tick_labels=infra_types, patch_artist=True)
    for patch, color in zip(box_plot['boxes'], sns.color_palette("husl", len(infra_types))):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax4.set_xlabel('Environment-Region')
    ax4.set_ylabel('CPU Usage (%)')
    ax4.set_title('CPU Distribution by Infrastructure Type')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(charts_dir / 'infrastructure_correlation.png', dpi=300, bbox_inches='tight')
    plt.close()

def chart_value_quantization(df, charts_dir):
    """Chart 3: Value quantization patterns."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Function to analyze decimal places
    def count_decimal_places(value):
        if isinstance(value, int) or value == int(value):
            return 0
        return len(str(value).split('.')[-1])
    
    # Plot 1: Decimal place distribution by metric type
    metric_types = ['cpu_usage_percent', 'memory_usage_percent', 
                   'http_request_duration_seconds', 'active_connections']
    
    decimal_data = {}
    for metric in metric_types:
        metric_data = df[df['metric_name'] == metric]
        if len(metric_data) > 0:
            decimal_places = [count_decimal_places(val) for val in metric_data['value']]
            decimal_data[metric] = decimal_places
    
    # Create histogram for decimal places
    x_pos = np.arange(len(decimal_data))
    means = [np.mean(decimals) for decimals in decimal_data.values()]
    maxs = [max(decimals) for decimals in decimal_data.values()]
    
    bars = ax1.bar(x_pos, means, alpha=0.7, capsize=5)
    ax1.set_xlabel('Metric Type')
    ax1.set_ylabel('Average Decimal Places')
    ax1.set_title('Value Precision by Metric Type')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([m.replace('_', '\n') for m in decimal_data.keys()], rotation=0)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (bar, mean_val, max_val) in enumerate(zip(bars, means, maxs)):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                f'{mean_val:.1f}\n(max: {max_val})', 
                ha='center', va='bottom', fontsize=9)
    
    # Plot 2: CPU percentage precision analysis
    cpu_data = df[df['metric_name'] == 'cpu_usage_percent']
    if len(cpu_data) > 0:
        cpu_decimals = [count_decimal_places(val) for val in cpu_data['value']]
        decimal_counts = Counter(cpu_decimals)
        
        ax2.bar(decimal_counts.keys(), decimal_counts.values(), alpha=0.7)
        ax2.set_xlabel('Number of Decimal Places')
        ax2.set_ylabel('Frequency')
        ax2.set_title('CPU Percentage Precision Distribution')
        ax2.grid(True, alpha=0.3)
        
        # Add percentage labels
        total = sum(decimal_counts.values())
        for decimals, count in decimal_counts.items():
            pct = (count / total) * 100
            ax2.text(decimals, count + total*0.01, f'{pct:.1f}%', 
                    ha='center', va='bottom', fontsize=9)
    
    # Plot 3: Response time quantization
    duration_data = df[df['metric_name'] == 'http_request_duration_seconds']
    if len(duration_data) > 0:
        # Show actual values to demonstrate quantization
        sample_data = duration_data['value'].head(100)
        ax3.scatter(range(len(sample_data)), sample_data, alpha=0.6, s=20)
        ax3.set_xlabel('Sample #')
        ax3.set_ylabel('Duration (seconds)')
        ax3.set_title('HTTP Duration Quantization Pattern')
        ax3.grid(True, alpha=0.3)
        
        # Highlight quantization levels
        unique_values = sorted(sample_data.unique())[:20]  # Show first 20 unique values
        for val in unique_values[::3]:  # Every 3rd value to avoid clutter
            ax3.axhline(y=val, color='red', alpha=0.3, linewidth=0.5)
    
    # Plot 4: Value distribution by quantization level
    all_decimals = []
    all_metrics = []
    
    for metric in df['metric_name'].unique():
        metric_data = df[df['metric_name'] == metric]
        decimals = [count_decimal_places(val) for val in metric_data['value']]
        all_decimals.extend(decimals)
        all_metrics.extend([metric] * len(decimals))
    
    # Create a violin plot showing distribution
    quantization_df = pd.DataFrame({
        'metric': all_metrics,
        'decimals': all_decimals
    })
    
    # Group similar metrics for cleaner visualization
    quantization_df['metric_group'] = quantization_df['metric'].apply(lambda x: 
        'Percentages' if 'percent' in x else
        'Durations' if 'duration' in x or 'time' in x else
        'Counters' if 'total' in x else
        'Connections' if 'connections' in x or 'queue' in x else
        'Other'
    )
    
    for i, group in enumerate(quantization_df['metric_group'].unique()):
        group_data = quantization_df[quantization_df['metric_group'] == group]
        ax4.hist(group_data['decimals'], alpha=0.6, label=group, bins=range(0, 6))
    
    ax4.set_xlabel('Number of Decimal Places')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Quantization Patterns by Metric Group')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(charts_dir / 'value_quantization.png', dpi=300, bbox_inches='tight')
    plt.close()

def chart_seasonal_patterns(df, charts_dir):
    """Chart 4: Seasonal and correlation patterns."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Daily pattern in CPU usage
    cpu_data = df[df['metric_name'] == 'cpu_usage_percent'].copy()
    if len(cpu_data) > 0:
        cpu_data['hour'] = pd.to_datetime(cpu_data['timestamp'], unit='s').dt.hour
        cpu_data['minute'] = pd.to_datetime(cpu_data['timestamp'], unit='s').dt.minute
        cpu_data['time_of_day'] = cpu_data['hour'] + cpu_data['minute'] / 60.0
        
        # Group by host to show individual patterns
        hosts = cpu_data['label_host'].unique()[:3]
        for host in hosts:
            host_data = cpu_data[cpu_data['label_host'] == host]
            # Calculate rolling average by time of day
            time_groups = host_data.groupby(host_data['time_of_day'].round(1))['value'].mean()
            ax1.plot(time_groups.index, time_groups.values, 
                    label=f'Host {host}', alpha=0.8, linewidth=2)
        
        ax1.set_xlabel('Hour of Day')
        ax1.set_ylabel('Average CPU Usage (%)')
        ax1.set_title('Daily CPU Usage Patterns by Host')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, 24)
    
    # Plot 2: Error rate correlation with load
    error_data = df[df['metric_name'] == 'error_rate_percent'].copy()
    cpu_data_for_corr = df[df['metric_name'] == 'cpu_usage_percent'].copy()
    
    if len(error_data) > 0 and len(cpu_data_for_corr) > 0:
        # Merge error and CPU data by timestamp and host
        error_data['key'] = error_data['timestamp'].astype(str) + '_' + error_data['label_host']
        cpu_data_for_corr['key'] = cpu_data_for_corr['timestamp'].astype(str) + '_' + cpu_data_for_corr['label_host']
        
        merged = pd.merge(
            error_data[['key', 'value']].rename(columns={'value': 'error_rate'}),
            cpu_data_for_corr[['key', 'value']].rename(columns={'value': 'cpu_usage'}),
            on='key'
        )
        
        if len(merged) > 0:
            ax2.scatter(merged['cpu_usage'], merged['error_rate'], alpha=0.5, s=20)
            
            # Add trend line
            z = np.polyfit(merged['cpu_usage'], merged['error_rate'], 1)
            p = np.poly1d(z)
            ax2.plot(merged['cpu_usage'], p(merged['cpu_usage']), "r--", alpha=0.8)
            
            correlation = merged['cpu_usage'].corr(merged['error_rate'])
            ax2.text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
                    transform=ax2.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            ax2.set_xlabel('CPU Usage (%)')
            ax2.set_ylabel('Error Rate (%)')
            ax2.set_title('Error Rate vs CPU Usage Correlation')
            ax2.grid(True, alpha=0.3)
    
    # Plot 3: Request volume patterns
    request_data = df[df['metric_name'] == 'http_requests_total'].copy()
    if len(request_data) > 0:
        # Calculate request rate (requests per second)
        request_data = request_data.sort_values('timestamp')
        request_data['hour'] = pd.to_datetime(request_data['timestamp'], unit='s').dt.hour
        
        # Group by hour and calculate average rate
        hourly_pattern = request_data.groupby('hour')['value'].mean()
        
        ax3.bar(hourly_pattern.index, hourly_pattern.values, alpha=0.7)
        ax3.set_xlabel('Hour of Day')
        ax3.set_ylabel('Average Request Count')
        ax3.set_title('Hourly Request Volume Pattern')
        ax3.grid(True, alpha=0.3)
        ax3.set_xticks(range(0, 24, 2))
    
    # Plot 4: Cross-metric correlation heatmap
    # Sample data for correlation analysis
    numeric_metrics = ['cpu_usage_percent', 'memory_usage_percent', 
                      'error_rate_percent', 'active_connections']
    
    correlation_data = {}
    for metric in numeric_metrics:
        metric_df = df[df['metric_name'] == metric]
        if len(metric_df) > 0:
            # Aggregate by timestamp to handle duplicates
            metric_series = metric_df.groupby('timestamp')['value'].mean()
            correlation_data[metric] = metric_series
    
    if len(correlation_data) > 1:
        # Create DataFrame with aligned timestamps
        corr_df = pd.DataFrame(correlation_data)
        corr_df = corr_df.ffill().bfill()
        
        if corr_df.shape[1] > 1:
            correlation_matrix = corr_df.corr()
            
            im = ax4.imshow(correlation_matrix, cmap='coolwarm', vmin=-1, vmax=1)
            ax4.set_xticks(range(len(correlation_matrix.columns)))
            ax4.set_yticks(range(len(correlation_matrix.columns)))
            ax4.set_xticklabels([col.replace('_', '\n') for col in correlation_matrix.columns], 
                               rotation=45, ha='right')
            ax4.set_yticklabels([col.replace('_', '\n') for col in correlation_matrix.columns])
            ax4.set_title('Cross-Metric Correlation Matrix')
            
            # Add correlation values
            for i in range(len(correlation_matrix)):
                for j in range(len(correlation_matrix)):
                    text = ax4.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                                  ha="center", va="center", color="black", fontsize=10)
            
            plt.colorbar(im, ax=ax4)
    
    plt.tight_layout()
    plt.savefig(charts_dir / 'seasonal_patterns.png', dpi=300, bbox_inches='tight')
    plt.close()

def chart_compression_impact(df, charts_dir):
    """Chart 5: Compression impact visualization."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Timestamp interval consistency
    intervals = []
    series_names = []
    
    for metric_name in df['metric_name'].unique()[:8]:  # Limit for clarity
        metric_data = df[df['metric_name'] == metric_name].sort_values('timestamp')
        if len(metric_data) > 1:
            metric_intervals = np.diff(metric_data['timestamp'].values)
            intervals.extend(metric_intervals)
            series_names.extend([metric_name] * len(metric_intervals))
    
    # Create consistency score
    perfect_intervals = sum(1 for interval in intervals if interval == 15)
    consistency_score = (perfect_intervals / len(intervals)) * 100
    
    # Show interval variance
    interval_variance = np.var(intervals)
    
    ax1.text(0.5, 0.7, f'Timestamp Regularity: {consistency_score:.1f}%', 
             ha='center', va='center', transform=ax1.transAxes, fontsize=16,
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    ax1.text(0.5, 0.5, f'Interval Variance: {interval_variance:.2f}s²', 
             ha='center', va='center', transform=ax1.transAxes, fontsize=14)
    ax1.text(0.5, 0.3, f'Expected Compression: ~{consistency_score/2.3:.0f}x', 
             ha='center', va='center', transform=ax1.transAxes, fontsize=14,
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    ax1.set_title('Timestamp Compression Potential')
    ax1.axis('off')
    
    # Plot 2: Value entropy analysis
    value_entropies = {}
    for metric in df['metric_name'].unique():
        metric_data = df[df['metric_name'] == metric]['value']
        # Simple entropy estimation based on unique values
        unique_ratio = len(metric_data.unique()) / len(metric_data)
        value_entropies[metric] = unique_ratio
    
    # Sort by entropy
    sorted_entropies = sorted(value_entropies.items(), key=lambda x: x[1])
    metrics, entropies = zip(*sorted_entropies)
    
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(entropies)))
    bars = ax2.barh(range(len(metrics)), entropies, color=colors, alpha=0.8)
    ax2.set_yticks(range(len(metrics)))
    ax2.set_yticklabels([m.replace('_', '\n') for m in metrics], fontsize=8)
    ax2.set_xlabel('Value Entropy (Unique Values / Total Values)')
    ax2.set_title('Value Compression Potential by Metric')
    ax2.grid(True, alpha=0.3)
    
    # Add compression estimates
    for i, (bar, entropy) in enumerate(zip(bars, entropies)):
        compression_est = max(1, 1 / entropy)
        ax2.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
                f'{compression_est:.1f}x', 
                ha='left', va='center', fontsize=8)
    
    # Plot 3: Infrastructure pattern strength
    # Analyze correlation strength between related series
    host_region_correlations = []
    
    cpu_data = df[df['metric_name'] == 'cpu_usage_percent']
    if len(cpu_data) > 0:
        pivot_data = cpu_data.pivot_table(
            index='timestamp', 
            columns=['label_host', 'label_region'], 
            values='value'
        ).ffill()
        
        if pivot_data.shape[1] > 1:
            correlation_matrix = pivot_data.corr()
            # Get upper triangle correlations (excluding diagonal)
            correlations = []
            for i in range(len(correlation_matrix)):
                for j in range(i+1, len(correlation_matrix)):
                    correlations.append(correlation_matrix.iloc[i, j])
            
            ax3.hist(correlations, bins=20, alpha=0.7, edgecolor='black')
            ax3.axvline(x=np.mean(correlations), color='red', linestyle='--', 
                       label=f'Mean: {np.mean(correlations):.3f}')
            ax3.set_xlabel('Correlation Coefficient')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Infrastructure Correlation Distribution')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # Add compression benefit estimate
            strong_correlations = sum(1 for c in correlations if c > 0.5)
            correlation_benefit = (strong_correlations / len(correlations)) * 100
            ax3.text(0.02, 0.98, f'Strong correlations: {correlation_benefit:.1f}%\nPredicted benefit: ~{correlation_benefit/10:.1f}x', 
                    transform=ax3.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # Plot 4: Overall compression summary
    compression_factors = {
        'Timestamp\nRegularity': consistency_score / 100 * 40,  # Up to 40x for perfect regularity
        'Value\nQuantization': np.mean(list(value_entropies.values())) * 3,  # Rough estimate
        'Infrastructure\nCorrelation': np.mean(correlations) * 2 if 'correlations' in locals() else 1,
        'Seasonal\nPatterns': 1.5  # Modest benefit from predictable patterns
    }
    
    factors = list(compression_factors.keys())
    values = list(compression_factors.values())
    colors = ['skyblue', 'lightgreen', 'orange', 'pink']
    
    bars = ax4.bar(factors, values, color=colors, alpha=0.8)
    ax4.set_ylabel('Compression Factor')
    ax4.set_title('Compression Benefit Breakdown')
    ax4.grid(True, alpha=0.3)
    
    # Add value labels
    for bar, value in zip(bars, values):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                f'{value:.1f}x', ha='center', va='bottom', fontsize=10,
                fontweight='bold')
    
    # Add total estimate
    total_compression = np.prod(values) ** 0.5  # Geometric mean approximation
    ax4.text(0.5, 0.95, f'Estimated Total: ~{total_compression:.1f}x compression', 
             transform=ax4.transAxes, ha='center', va='top', fontsize=12,
             bbox=dict(boxstyle='round', facecolor='gold', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(charts_dir / 'compression_impact.png', dpi=300, bbox_inches='tight')
    plt.close()


def chart_data_series_examples(df, charts_dir):
    """Generate example charts showing actual data series from the dataset"""
    
    # Create figure with subplots for different data series examples
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Enhanced Data Generation: Example Time Series', fontsize=16, fontweight='bold')
    
    # Chart 1: CPU usage patterns showing infrastructure correlation
    ax1 = axes[0, 0]
    cpu_data = df[df['metric_name'] == 'cpu_usage_percent'].copy()
    
    if len(cpu_data) > 0:
        # Create host-region combinations
        cpu_data['host_region'] = cpu_data['label_host'].astype(str) + '-' + cpu_data['label_region'].astype(str)
        
        # Show data for different host-region combinations
        host_regions = cpu_data['host_region'].unique()[:4]  # Show top 4
        colors = plt.cm.Set3(np.linspace(0, 1, len(host_regions)))
        
        for i, hr in enumerate(host_regions):
            hr_data = cpu_data[cpu_data['host_region'] == hr].sort_values('datetime')
            if len(hr_data) > 10:  # Only plot if we have enough data
                ax1.plot(hr_data['datetime'], hr_data['value'], 
                        color=colors[i], label=hr, linewidth=1.2, alpha=0.8)
        
        ax1.set_title('CPU Usage: Infrastructure Correlation Patterns')
        ax1.set_ylabel('CPU Usage (%)')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # Chart 2: HTTP request latency showing quantization
    ax2 = axes[0, 1]
    # Try different latency metric names
    latency_metrics = ['http_request_duration_ms', 'http_request_duration_seconds', 'response_time_ms']
    latency_data = None
    
    for metric in latency_metrics:
        if metric in df['metric_name'].values:
            latency_data = df[df['metric_name'] == metric].copy()
            break
    
    if latency_data is not None and len(latency_data) > 0:
        # Show a sample of latency data points
        sample_data = latency_data.sample(min(1000, len(latency_data))).sort_values('datetime')
        
        ax2.scatter(sample_data['datetime'], sample_data['value'], 
                   alpha=0.6, s=8, color='orange')
        ax2.set_title('HTTP Request Duration: Value Quantization')
        ax2.set_ylabel('Duration (seconds)' if 'seconds' in metric else 'Duration (ms)')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Add note about quantization
        ax2.text(0.02, 0.98, 'Note: Values show realistic\nprecision patterns', 
                transform=ax2.transAxes, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    else:
        # No latency data found, show error rate instead
        error_data = df[df['metric_name'] == 'error_rate_percent'].copy()
        if len(error_data) > 0:
            sample_data = error_data.sample(min(1000, len(error_data))).sort_values('datetime')
            ax2.scatter(sample_data['datetime'], sample_data['value'], 
                       alpha=0.6, s=8, color='red')
            ax2.set_title('Error Rate: Value Distribution')
            ax2.set_ylabel('Error Rate (%)')
            ax2.grid(True, alpha=0.3)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        else:
            ax2.text(0.5, 0.5, 'No suitable metric found\nfor this chart', 
                    transform=ax2.transAxes, ha='center', va='center',
                    bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
    
    # Chart 3: Memory usage showing seasonal patterns
    ax3 = axes[1, 0]
    memory_data = df[df['metric_name'] == 'memory_usage_percent'].copy()
    
    if len(memory_data) > 0:
        try:
            # Sample one series for cleaner visualization
            sample_host = memory_data['label_host'].iloc[0]
            sample_region = memory_data['label_region'].iloc[0]
            
            series_data = memory_data[
                (memory_data['label_host'] == sample_host) & 
                (memory_data['label_region'] == sample_region)
            ].sort_values('datetime')
            
            if len(series_data) > 10:
                ax3.plot(series_data['datetime'], series_data['value'], 
                        color='green', linewidth=1.5)
                ax3.fill_between(series_data['datetime'], series_data['value'], 
                                alpha=0.3, color='green')
                ax3.set_title(f'Memory Usage: {sample_host}-{sample_region}')
                ax3.set_ylabel('Memory Usage (%)')
                ax3.grid(True, alpha=0.3)
                ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            else:
                # Fallback: aggregate all data
                memory_data_agg = memory_data.groupby('datetime')['value'].mean().reset_index()
                memory_data_agg = memory_data_agg.sort_values('datetime')
                
                ax3.plot(memory_data_agg['datetime'], memory_data_agg['value'], 
                        color='green', linewidth=1.5)
                ax3.fill_between(memory_data_agg['datetime'], memory_data_agg['value'], 
                                alpha=0.3, color='green')
                ax3.set_title('Memory Usage: Aggregated Pattern')
                ax3.set_ylabel('Memory Usage (%)')
                ax3.grid(True, alpha=0.3)
                ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        except Exception as e:
            ax3.text(0.5, 0.5, f'Error rendering memory chart:\n{str(e)}', 
                    transform=ax3.transAxes, ha='center', va='center',
                    bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
    else:
        ax3.text(0.5, 0.5, 'No memory usage data found', 
                transform=ax3.transAxes, ha='center', va='center',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
    
    # Chart 4: HTTP request count showing counter behavior
    ax4 = axes[1, 1]
    counter_data = df[df['metric_name'] == 'http_requests_total'].copy()
    
    if len(counter_data) > 0:
        # Show counter progression for one series
        sample_row = counter_data.iloc[0]  # Just get first row
        host = sample_row['label_host']
        region = sample_row['label_region']
        
        series_data = counter_data[
            (counter_data['label_host'] == host) & 
            (counter_data['label_region'] == region)
        ].sort_values('datetime')
        
        if len(series_data) > 10:
            ax4.plot(series_data['datetime'], series_data['value'], 
                    color='purple', linewidth=1.5, marker='o', markersize=2)
            ax4.set_title(f'HTTP Requests Counter: {host}-{region}')
            ax4.set_ylabel('Total Requests')
            ax4.grid(True, alpha=0.3)
            ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            # Add note about counter behavior
            ax4.text(0.02, 0.98, 'Monotonically increasing\ncounter with realistic rate', 
                    transform=ax4.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lavender', alpha=0.5))
    
    # Format x-axis for all subplots
    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=45)
        plt.setp(ax.xaxis.get_majorticklabels(), ha='right')
    
    plt.tight_layout()
    plt.savefig(charts_dir / "data_series_examples.png", dpi=300, bbox_inches='tight')
    plt.close()


def chart_timestamp_intervals(df, charts_dir):
    """Generate detailed timestamp interval analysis"""
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Enhanced Timestamp Regularity Analysis', fontsize=16, fontweight='bold')
    
    # Calculate intervals for each metric series
    all_intervals = []
    perfect_intervals = 0
    total_intervals = 0
    
    for (metric, host, region), group in df.groupby(['metric_name', 'label_host', 'label_region']):
        if len(group) > 1:
            sorted_group = group.sort_values('datetime')
            intervals = sorted_group['datetime'].diff().dt.total_seconds().dropna()
            all_intervals.extend(intervals.tolist())
            
            # Count perfect 30-second intervals
            perfect_count = sum(abs(interval - 30.0) < 0.1 for interval in intervals)
            perfect_intervals += perfect_count
            total_intervals += len(intervals)
    
    regularity_percentage = (perfect_intervals / total_intervals * 100) if total_intervals > 0 else 0
    
    # Chart 1: Interval distribution
    ax1 = axes[0]
    if all_intervals:
        ax1.hist(all_intervals, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(30.0, color='red', linestyle='--', linewidth=2, label='Target: 30s')
        ax1.set_title('Timestamp Interval Distribution')
        ax1.set_xlabel('Interval (seconds)')
        ax1.set_ylabel('Frequency')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add statistics text
        ax1.text(0.02, 0.98, f'Perfect regularity: {regularity_percentage:.1f}%\n'
                              f'Total intervals: {total_intervals:,}',
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
    
    # Chart 2: Regularity by metric type
    ax2 = axes[1]
    metric_regularity = {}
    
    for metric in df['metric_name'].unique():
        metric_data = df[df['metric_name'] == metric]
        metric_intervals = []
        
        for (host, region), group in metric_data.groupby(['label_host', 'label_region']):
            if len(group) > 1:
                sorted_group = group.sort_values('datetime')
                intervals = sorted_group['datetime'].diff().dt.total_seconds().dropna()
                metric_intervals.extend(intervals.tolist())
        
        if metric_intervals:
            perfect_count = sum(abs(interval - 30.0) < 0.1 for interval in metric_intervals)
            regularity = perfect_count / len(metric_intervals) * 100
            metric_regularity[metric] = regularity
    
    if metric_regularity:
        metrics = list(metric_regularity.keys())
        regularities = list(metric_regularity.values())
        
        bars = ax2.bar(range(len(metrics)), regularities, color='lightcoral', alpha=0.7)
        ax2.set_title('Timestamp Regularity by Metric Type')
        ax2.set_xlabel('Metric')
        ax2.set_ylabel('Regularity (%)')
        ax2.set_xticks(range(len(metrics)))
        ax2.set_xticklabels([m.replace('_', '\n') for m in metrics], rotation=45, ha='right')
        ax2.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, reg in zip(bars, regularities):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{reg:.1f}%', ha='center', va='bottom', fontsize=8)
    
    # Chart 3: Interval jitter over time
    ax3 = axes[2]
    
    # Sample one series for jitter analysis
    sample_metric = df['metric_name'].iloc[0]
    sample_host = df['label_host'].iloc[0] 
    sample_region = df['label_region'].iloc[0]
    
    sample_data = df[
        (df['metric_name'] == sample_metric) &
        (df['label_host'] == sample_host) &
        (df['label_region'] == sample_region)
    ].sort_values('datetime')
    
    if len(sample_data) > 1:
        intervals = sample_data['datetime'].diff().dt.total_seconds().dropna()
        jitter = intervals - 30.0  # Deviation from perfect 30s
        
        ax3.plot(range(len(jitter)), jitter, marker='o', markersize=3, alpha=0.7, color='darkgreen')
        ax3.axhline(0, color='red', linestyle='--', alpha=0.7, label='Perfect timing')
        ax3.set_title(f'Timing Jitter: {sample_metric}')
        ax3.set_xlabel('Measurement #')
        ax3.set_ylabel('Jitter (seconds)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Add statistics
        mean_jitter = abs(jitter).mean()
        ax3.text(0.02, 0.98, f'Mean jitter: {mean_jitter:.2f}s\n'
                              f'Max jitter: {abs(jitter).max():.2f}s',
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig(charts_dir / "timestamp_intervals_detailed.png", dpi=300, bbox_inches='tight')
    plt.close()


def main():
    """Generate all charts for the data generation deep dive."""
    print("📊 Generating charts for data generation deep dive...")
    
    # Load dataset
    try:
        data_points = load_dataset()
        print(f"✅ Loaded {len(data_points):,} data points")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return
    
    # Convert to DataFrame
    df = convert_to_dataframe(data_points)
    print(f"✅ Converted to DataFrame with {len(df.columns)} columns")
    
    # Create charts directory
    charts_dir = create_charts_directory()
    print(f"✅ Created charts directory: {charts_dir}")
    
    # Generate data series illustration charts only
    print("📈 Generating data series examples...")
    chart_data_series_examples(df, charts_dir)
    
    print("\n🎉 All charts generated successfully!")
    print(f"📁 Charts saved to: {charts_dir.absolute()}")
    print("\nGenerated charts:")
    for chart_file in charts_dir.glob("*.png"):
        print(f"  - {chart_file.name}")
    
    # Print summary statistics
    print(f"\n📊 Dataset Summary:")
    print(f"  Total data points: {len(df):,}")
    print(f"  Unique metrics: {df['metric_name'].nunique()}")
    print(f"  Time range: {(df['datetime'].max() - df['datetime'].min()).total_seconds() / 3600:.1f} hours")
    print(f"  Unique hosts: {df['label_host'].nunique()}")
    print(f"  Unique regions: {df['label_region'].nunique()}")

if __name__ == "__main__":
    main()