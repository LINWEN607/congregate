from helpers import base_module as b
from multiprocessing.dummy import Pool as ThreadPool

def handle_multi_thread(function, data):
    pool = ThreadPool(b.config.threads)
    results = pool.map(function, data)
    pool.close()
    pool.join()
    return results