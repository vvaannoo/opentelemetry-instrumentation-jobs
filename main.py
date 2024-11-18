import logging
import os
import random
import time

import schedule


from opentelemetry_python_instrumentation_jobs import send_metrics

SERVICE_NAME = os.getenv('OTEL_SERVICE_NAME')

logger = logging.getLogger(SERVICE_NAME)


@send_metrics(job_name="job 1")
def job_1(*args, **kwargs):
    execute_job(*args, **kwargs)


@send_metrics(job_name="job 2")
def job_2(*args, **kwargs):
    execute_job(*args, **kwargs)


def execute_job(update_progress: callable = None, **kwargs):
    total = random.choice([50, 100, 150, 200, 250])
    batch_size = 50
    for i in range(0, total, batch_size):
        time.sleep(random.randint(3, 10))
        if 5 == random.randint(1, 100):
            raise Exception("error")
        current_batch = min(batch_size, total - i)
        update_progress(current_batch, total)


schedule.every(1).minutes.do(job_1)
schedule.every(20).seconds.do(job_2)

for job in schedule.jobs:
    logger.info(str(job))

while True:
    schedule.run_pending()
    time.sleep(1)
