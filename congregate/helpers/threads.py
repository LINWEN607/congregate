from multiprocessing import Pool, cpu_count
from multiprocessing.dummy import Pool as ThreadPool
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import json_pretty

b = BaseClass()


def handle_multi_thread(function, data, threads=None):
    try:
        p = ThreadPool(processes=get_no_of_processes(threads))
        return p.map(function, data)
    except Exception as e:
        b.log.error("Multi thread failed with error:\n{}".format(e))
    finally:
        p.close()
        p.join()


def start_multi_process(function, iterable, threads=None):
    try:
        p = Pool(processes=get_no_of_processes(threads))
        return p.map(function, iterable)
    except Exception as e:
        b.log.error("Migration pool failed with error:\n{}".format(e))
    finally:
        p.close()
        p.join()


def handle_multi_thread_write_to_file_and_return_results(function, results_function, data, path, threads=None):
    p = ThreadPool(processes=get_no_of_processes(threads))
    with open(path, 'w') as f:
        f.write("[\n")
        try:
            for result in p.imap_unordered(function, data):
                f.write(json_pretty(result))
                yield results_function(result)
        except TypeError as te:
            print("Found None ({}). Stopping write to file".format(te))
        except Exception as e:
            b.log.error("Migration thread failed with error:\n{}".format(e))
        else:
            f.write("\n]")
        finally:
            p.close()
            p.join()


def get_no_of_processes(threads):
    return threads if threads else cpu_count()-1
