from congregate.helpers.base_class import BaseClass
from multiprocessing.dummy import Pool as ThreadPool

b = BaseClass()


def handle_multi_thread(function, data):
    pool = ThreadPool(b.config.threads)
    results = pool.map(function, data)
    pool.close()
    pool.join()
    return results
