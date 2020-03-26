from multiprocessing.dummy import Pool as ThreadPool
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import json_pretty

b = BaseClass()


def handle_multi_thread(function, data):
    pool = ThreadPool(b.config.threads)
    results = pool.map(function, data)
    pool.close()
    pool.join()
    return results


def handle_multi_thread_write_to_file_and_return_results(function, results_function, data, path):
    pool = ThreadPool(b.config.threads)
    results = []
    with open(path, 'w') as f:
        f.write("[\n")
        try:
            for result in pool.imap_unordered(function, data):
                results.append(results_function(result))
                f.write(json_pretty(result))
        except TypeError as te:
            print("Found None ({}). Stopping write to file".format(te))
        f.write("\n]")
    return results
