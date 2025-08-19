#!/usr/bin/env python3
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from tabulate import tabulate


class LogProcessor:
    
    def __init__(self):
        self.data = defaultdict(list)
    
    def read_log_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            log_entry = json.loads(line)
                            self._process_log_entry(log_entry)
                        except json.JSONDecodeError:
                            print(f"Warning: Invalid JSON in line: {line}", 
                                  file=sys.stderr)
        except FileNotFoundError:
            print(f"Error: File {file_path} not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _process_log_entry(self, log_entry):
        url = log_entry.get('url')
        response_time = log_entry.get('response_time')
        timestamp = log_entry.get('@timestamp')
        
        if url and response_time is not None:
            self.data[url].append({
                'response_time': response_time,
                'timestamp': timestamp
            })
    
    def filter_by_date(self, target_date):
        if not target_date:
            return
        
        filtered_data = defaultdict(list)
        try:
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            
            for url, entries in self.data.items():
                for entry in entries:
                    if entry['timestamp']:
                        try:
                            entry_date = datetime.fromisoformat(
                                entry['timestamp'].replace('Z', '+00:00')
                            ).date()
                            if entry_date == target_date_obj:
                                filtered_data[url].append(entry)
                        except (ValueError, TypeError):
                            continue
        
            self.data = filtered_data
        except ValueError:
            print(f"Error: Invalid date format {target_date}. Use YYYY-MM-DD",
                  file=sys.stderr)
            sys.exit(1)
    
    def generate_average_report(self):
        report_data = []
        
        for url, entries in self.data.items():
            if entries:
                total_requests = len(entries)
                total_response_time = sum(entry['response_time'] for entry in entries)
                avg_response_time = total_response_time / total_requests
                
                report_data.append({
                    'url': url, 
                    'total_requests': total_requests,
                    'avg_response_time': round(avg_response_time, 3)
                })
        
        report_data.sort(key=lambda x: x['total_requests'], reverse=True)
        
        return report_data


class ReportGenerator:
    
    @staticmethod
    def generate_report(processor, report_type, **kwargs):
        if report_type == 'average':
            return ReportGenerator._generate_average_report(processor, **kwargs)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    @staticmethod
    def _generate_average_report(processor, **kwargs):
        report_data = processor.generate_average_report()
        
        table_data = []
        for i, item in enumerate(report_data):
            table_data.append([
                i,
                item['url'],
                item['total_requests'],
                item['avg_response_time']
            ])
        
        headers = ['#', 'Endpoint', 'Total Requests', 'Avg Response Time']
        return tabulate(table_data, headers=headers, tablefmt='grid')


def main():
    parser = argparse.ArgumentParser(
        description='Process log files and generate reports'
    )
    parser.add_argument(
        '--file', 
        nargs='+', 
        required=True,
        help='Path to log file(s) (multiple files allowed)'
    )
    parser.add_argument(
        '--report', 
        required=True,
        choices=['average'],
        help='Type of report to generate'
    )
    parser.add_argument(
        '--date',
        help='Filter logs by specific date (format: YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    processor = LogProcessor()
    
    for file_path in args.file:
        processor.read_log_file(file_path)
    
    if args.date:
        processor.filter_by_date(args.date)
    
    try:
        report = ReportGenerator.generate_report(
            processor, 
            args.report
        )
        print(report)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()