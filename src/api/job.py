from api.scrapers.aws import awsBulk
from api.scrapers.azure import retail

from apscheduler.schedulers.background import BackgroundScheduler

import requests


def heartbeat():
    requests.get('http://localhost:5042/health')


def aws_download_job():
    awsBulk.download_file()


def azure_download_job():
    retail.download_file()


def azure_vm_size_download_job():
    retail.scrape_size()


def load_job():
    retail.load_file()
    awsBulk.load_file()


def run_scheduler():
    sched.start()


sched = BackgroundScheduler(daemon=True)
sched.add_job(aws_download_job, 'interval', days=29)
sched.add_job(azure_download_job, 'interval', days=29)
sched.add_job(load_job, 'interval', days=30)
sched.add_job(azure_vm_size_download_job, 'interval', weeks=52)
