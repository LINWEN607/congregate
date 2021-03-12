from traceback import print_exc
from multiprocessing import Pool, cpu_count, get_context
from functools import partial
from tqdm import tqdm
from congregate.helpers.misc_utils import json_pretty
from congregate.helpers.base_class import BaseClass
from congregate.helpers.process import NoDaemonProcess

b = BaseClass()
_func = None
tanuki = "#e24329"


def worker_init(func):
    global _func
    _func = func


def worker(x):
    return _func(x)


def start_multi_process(function, iterable, processes=None):
    """
        Wrapper function to handle multiprocessing a function with a list of data

        This function leverages map to handle multiprocessing. This function will return a list of data from the function so use this function if your function returns necessary data

        :param: function: (func) The function processesing the elements of the list
        :param: iterable: (list) A list of data to be passed into the function to process
        :param: processes: (int) Explicit number of processes to split the function across. If processes is not set, number of processes will default to total number of physical cores of CPU

        :return: A list of the data returned from the process map
    """
    ctx = get_context("spawn")
    ctx.Process = NoDaemonProcess
    p = ctx.Pool(processes=get_no_of_processes(processes),
                 initializer=worker_init, initargs=(function,))
    try:
        for i in tqdm(p.imap_unordered(worker, iterable), total=len(iterable), colour=tanuki):
            yield i
    except Exception as e:
        b.log.critical("Migration pool failed with error:\n{}".format(e))
        b.log.critical(print_exc())
    finally:
        p.close()
        p.join()


def start_multi_process_with_args(function, iterable, *args, processes=None):
    """
        Wrapper function to handle multiprocessing a function with multiple arguments with a list of data

        This function leverages map to handle multiprocessing. This function will return a list of data from the function so use this function if your function returns necessary data

        :param: function: (func) The function processesing the elements of the list
        :param: iterable: (list) A list of data to be passed into the function to process
        :param: *args: (args) Any additional arguments the function needs passed in
        :params processes: (int) Explicit number of processes to split the function across. If processes is not set, number of processes will default to total number of physical cores of CPU

        :return: A list of the data returned from the process map
    """
    ctx = get_context("spawn")
    p = ctx.Pool(processes=get_no_of_processes(processes),
                 initializer=worker_init, initargs=(partial(function, *args),))
    try:
        for i in tqdm(p.imap_unordered(worker, iterable), total=len(iterable), colour=tanuki):
            yield i
    except Exception as e:
        b.log.critical("Migration pool failed with error:\n{}".format(e))
        b.log.critical(print_exc())
    finally:
        p.close()
        p.join()


def start_multi_process_stream(function, iterable, processes=None):
    """
        Wrapper function to handle multiprocessing a function with a list of data

        This function leverages imap_unordered to handle processing a stream of data of unknown length, like from a generator

        :param: function: (func) The function processesing the elements of the list
        :param: iterable: (list) A list of data to be passed into the function to process
        :param: processes: (int) Explicit number of processes to split the function across. If processes is not set, number of processes will default to total number of physical cores of CPU

        :return: An imap_unordered object. Assume no useful data will be returned with this function
    """
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
    """
        Wrapper function to handle multiprocessing a function with multiple arguments with a list of data

        This function leverages imap_unordered to handle processing a stream of data of unknown length, like from a generator

        :param: function: (func) The function processesing the elements of the list
        :param: iterable: (list) A list of data to be passed into the function to process
        :param: *args: (args) Any additional arguments the function needs passed in
        :param: processes: (int) Explicit number of processes to split the function across. If processes is not set, number of processes will default to total number of physical cores of CPU

        :return: An imap_unordered object. Assume no useful data will be returned with this function
    """
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
            for result in tqdm(p.imap_unordered(worker, iterable), total=len(iterable), colour=tanuki):
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
