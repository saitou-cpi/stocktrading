'''logging_setup.py'''
import os
import datetime
import logging

def setup_logging(symbol):
    log_dir = os.path.abspath("optimal_parameter_log")
    os.makedirs(log_dir, exist_ok=True)
    results_date_str = datetime.datetime.now().strftime('%Y%m%d%H%M')
    log_filename = os.path.join(log_dir, f'{symbol.replace(".", "_")}_optimal_parameter_{results_date_str}.log')
    logging.basicConfig(filename=log_filename, level=logging.INFO)
    return log_dir
