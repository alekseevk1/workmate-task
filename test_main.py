import pytest
import json
import tempfile
import os
from main import LogProcessor, ReportGenerator


@pytest.fixture
def sample_log_data():
    return [
        {
            "@timestamp": "2025-06-22T20:03:08+00:00",
            "status": 200,
            "url": "/api/homeworks/...",
            "request_method": "GET",
            "response_time": 0.02,
            "http_user_agent": "test-agent"
        },
        {
            "@timestamp": "2025-06-22T20:04:08+00:00",
            "status": 200,
            "url": "/api/homeworks/...",
            "request_method": "GET",
            "response_time": 0.04,
            "http_user_agent": "test-agent"
        },
        {
            "@timestamp": "2025-06-23T20:03:08+00:00",
            "status": 200,
            "url": "/api/users/...",
            "request_method": "GET",
            "response_time": 0.06,
            "http_user_agent": "test-agent"
        }
    ]


@pytest.fixture
def temp_log_file(sample_log_data):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        for entry in sample_log_data:
            f.write(json.dumps(entry) + '\n')
        temp_file = f.name
    
    yield temp_file
    os.unlink(temp_file)


def test_log_processor_read_file(temp_log_file):
    processor = LogProcessor()
    processor.read_log_file(temp_log_file)
    
    assert len(processor.data) == 2
    assert '/api/homeworks/...' in processor.data
    assert '/api/users/...' in processor.data
    assert len(processor.data['/api/homeworks/...']) == 2


def test_log_processor_filter_by_date(sample_log_data):
    processor = LogProcessor()
    for entry in sample_log_data:
        processor._process_log_entry(entry)
    
    assert len(processor.data['/api/homeworks/...']) == 2
    
    processor.filter_by_date('2025-06-22')
    
    assert len(processor.data['/api/homeworks/...']) == 2
    assert '/api/users/...' not in processor.data


def test_generate_average_report(sample_log_data):
    processor = LogProcessor()
    
    for entry in sample_log_data:
        processor._process_log_entry(entry)
    
    report_data = processor.generate_average_report()
    
    assert len(report_data) == 2
    
    homework_data = next(item for item in report_data if item['url'] == '/api/homeworks/...')
    assert homework_data['total_requests'] == 2
    assert homework_data['avg_response_time'] == 0.03  # (0.02 + 0.04) / 2


def test_report_generator():
    processor = LogProcessor()
    
    test_data = [
        {'url': '/api/test', 'response_time': 0.1, 'timestamp': '2025-06-22T20:03:08+00:00'},
        {'url': '/api/test', 'response_time': 0.2, 'timestamp': '2025-06-22T20:04:08+00:00'}
    ]
    
    for entry in test_data:
        processor._process_log_entry(entry)
    
    report = ReportGenerator.generate_report(processor, 'average')
    
    assert 'Endpoint' in report
    assert 'Total Requests' in report
    assert 'Avg Response Time' in report
    assert '/api/test' in report


def test_invalid_json_handling():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write('invalid json data\n')
        f.write('{"valid": "json"}\n')
        temp_file = f.name
    
    try:
        processor = LogProcessor()
        processor.read_log_file(temp_file)
        assert len(processor.data) == 0
    finally:
        os.unlink(temp_file)


def test_file_not_found():
    processor = LogProcessor()
    
    with pytest.raises(SystemExit):
        processor.read_log_file('nonexistent_file.log')