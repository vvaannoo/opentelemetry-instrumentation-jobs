# opentelemetry-python-instrumentation-jobs
This is a library that allows you to send metrics and logs of scheduled jobs in python to otel-collector.

Tested with python 3.12:
- schedule
- apscheduler

## Installation

```bash
pip install opentelemetry-python-instrumentation-jobs
```

## Usage

```python
from opentelemetry_python_instrumentation_jobs import send_metrics

@send_metrics(job_name="job 1")
def job_1(job_name: str, update_progress: Callable):
    total = 10
    for i in range(total):
        update_progress(1, total)
```

### `send_metrics` decorator

#### parameters:

- `job_name` (string): The name of the job
- `show_progress` (boolean): Whether to show the progress of the job in console(tqdm)

decorator injects `job_name` and `update_progress` parameters to the job function

`update_progress` is a function that takes two parameters:
- processed items count in the iteration (1 or batch size);
- total items count (10 in this example)

You can ignore `job_name` and `update_progress` parameters if you don't need them:

```python
from opentelemetry_python_instrumentation_jobs import send_metrics

@send_metrics(job_name="job 1")
def job_1(*args, **kwargs):
    for i in range(10):
        pass
```

## Environment Variables

- `OTEL_SERVICE_NAME` (string): The name of the service
- `OTEL_EXPORTER_OTLP_ENDPOINT` (string): The endpoint of the otel-collector
- `OTEL_EXPORTER_OTLP_INSECURE` (boolean): Whether to use insecure connection
- `SENDING_LOGS_AND_METRICS_ENABLED` (boolean): Whether to send logs and metrics
- `OTEL_EXPORT_INTERVAL` (int): The interval in milliseconds at which to export metrics

## Full example

```python
import time
import schedule
from opentelemetry_python_instrumentation_jobs import send_metrics

@send_metrics(job_name="job 1")
def job_1(*args, update_progress: Callable, **kwargs):
    total = 20
    update_progress(0, total)
    
    for i in range(total):
        time.sleep(1)
        update_progress(1, total)

@send_metrics(job_name="job 2", show_progress=False)
def job_2(*args, **kwargs): 
    for i in range(10):
        time.sleep(1)

schedule.every(1).minutes.do(job_1)
schedule.every(20).seconds.do(job_2)

while True:
    schedule.run_pending()
    time.sleep(1)
```


## Metrics that are sent

- `test_job_run_count` (counter): How many times the job has been run
- `test_job_status` (counter): Job counter by status (success, error)
- `test_job_duration` (gauge): Job execution duration in seconds
- `test_job_records` (gauge): Number of records in job (processed, total)
- `test_job_last_status` (gauge): Last job status (1, 0)
- `test_job_time` (gauge): Job start and finish time in unix timestamp (started, finished)


### License

MIT License

Copyright (c) 2024 Vano Atabegashvili
