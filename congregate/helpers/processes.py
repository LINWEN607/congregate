from traceback import print_exc
from multiprocessing import Pool, cpu_count, get_context
from functools import partial
from congregate.helpers.misc_utils import json_pretty
from congregate.helpers.base_class import BaseClass

b = BaseClass()
_func = None


def worker_init(func):
    global _func
    _func = func


def worker(x):
    return _func(x)


def start_multi_process(function, iterable, processes=None):
    ctx = get_context("spawn")
    p = ctx.Pool(processes=get_no_of_processes(processes),
                 initializer=worker_init, initargs=(function,))
    try:
        return p.map(worker, iterable)
    except Exception as e:
        b.log.critical("Migration pool failed with error:\n{}".format(e))
        b.log.critical(print_exc())
    finally:
        p.close()
        p.join()


def start_multi_process_stream(function, iterable, processes=None):
    ctx = get_context("spawn")
    p = ctx.Pool(processes=get_no_of_processes(processes),
                 initializer=worker_init, initargs=(function,))
    try:
        return p.imap_unordered(worker, iterable)
    except Exception as e:
        b.log.critical("Migration pool failed with error:\n{}".format(e))
        b.log.critical(print_exc())
    finally:
        p.close()
        p.join()


def start_multi_process_stream_with_args(function, iterable, *args, processes=None):
    ctx = get_context("spawn")
    p = ctx.Pool(processes=get_no_of_processes(processes),
                 initializer=worker_init, initargs=(partial(function, *args),))
    try:
        return p.imap_unordered(worker, iterable)
    except Exception as e:
        b.log.critical("Migration pool failed with error:\n{}".format(e))
        b.log.critical(print_exc())
    finally:
        p.close()
        p.join()


def handle_multi_process_write_to_file_and_return_results(function, results_function, iterable, path, processes=None):
    with open(path, 'w') as f:
        f.write("[\n")
        try:
            p = Pool(processes=get_no_of_processes(processes),
                     initializer=worker_init, initargs=(function,))
            for result in p.imap_unordered(worker, iterable):
                f.write(json_pretty(result))
                yield results_function(result)
        except TypeError as te:
            print_exc()
            print("Found None ({}). Stopping write to file".format(te))
        except Exception as e:
            b.log.critical(
                "Migration processes failed with error:\n{}".format(e))
            b.log.critical(print_exc())
        else:
            f.write("\n]")
        finally:
            p.close()
            p.join()


def get_no_of_processes(processes):
    try:
        return int(processes) if processes else cpu_count() - 1 or 1
    except ValueError:
        b.log.error(
            "Input for # of processes is not an integer: {}".format(processes))
        exit()
