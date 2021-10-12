import multiprocessing as mp
import threading
from functools import partial, reduce
import copy

import numpy as np

_process = None


def _func_helper(res, func, args):
    try:
        result = func(*args)
    except:
        print('Error in: parameter: "', args, '"')
        result = None
    res.append(result)


def _func_no_error(data):
    func, args = data
    try:
        result = func(*args)
    except:
        print('Error in: parameter: "', args, '"')
        result = None
    return result


def _func_simple(data):
    func, args = data
    result = func(*args)
    return result


def _abortable_worker(func, *args, **kwargs):
    res = []
    timeout = kwargs.get('timeout', None)
    t = threading.Thread(target=_func_helper, args=(res, func, args))
    t.start()
    t.join(timeout)
    if t.isAlive():
        print('Time out in: parameter: "', args[0], '"')
        return None

    if len(res) == 0:
        return None
    return res[0]


def _run_multiple_process_simple(func_run, func_para, **kwargs):
    global _process
    if not _process:
        _process = mp.Pool(Parameter.threads)
    # Build para
    run_para = [(func_run, p) for p in func_para]
    result = _process.map(_func_simple, run_para, **kwargs)
    return result


def _run_multiple_thread_time_out(func_run, func_para, func_timeout, **kwargs):
    global _process
    if not _process:
        _process = mp.Pool(Parameter.threads)

    run_para = [(partial(_abortable_worker, func_run, timeout=func_timeout, **kwargs), p) for p in func_para]
    result = _process.map(_func_simple, run_para, **kwargs)

    return result


def _run_multiple_process(func_run, func_para, **kwargs):
    global _process
    if not _process:
        _process = mp.Pool(Parameter.threads)
    # Build para
    run_para = [(func_run, p) for p in func_para]
    result = _process.map(_func_no_error, run_para, **kwargs)
    no_none_result = []
    for r in result:
        if r is not None:
            no_none_result.append(r)
    return no_none_result


def _run_multiple_para(func_run, func_para, return_queue):
    all_res = []
    for para in func_para:
        res = func_run(*para)
        all_res.append(res)
    return_queue.append(all_res)
    pass


def _func_worker(func_run, func_para_share, q_input, q_output):
    while not q_input.empty():
        try:
            q_item = q_input.get(block=True, timeout=1)
        except:
            continue
        i, para = q_item
        if func_para_share is not None:
            para += func_para_share

        try:
            result = func_run(*para)
        except Exception as e:
            result = None
            print(e)
        q_output.put((i, result))
    return


def _func_worker_no_auto_stop(func_run, func_para_share, q_input, q_output, copy_shared_para=False):
    if copy_shared_para:
        func_para_share = copy.deepcopy(func_para_share)

    while 1:
        try:
            q_item = q_input.get(block=True, timeout=1)
        except:
            continue

        if q_item is None:
            break

        i, para = q_item
        if func_para_share is not None:
            para += func_para_share

        try:
            result = func_run(*para)
        except Exception as e:
            result = None
            print(para, e)
        q_output.put((i, result))
    return


def run_multiple_process(func_run, func_merge=None, func_worker=None,
                         all_para_individual=(), para_share=None, threads=1):
    if func_merge is None:
        def func_merge(f_final_result, f_cur_result):
            if f_final_result is None:
                f_final_result = [f_cur_result]
            else:
                f_final_result.append(f_cur_result)
            return f_final_result

    if func_worker is None:
        func_worker = _func_worker_no_auto_stop

    q_input = mp.Queue()
    for cur_result_num, para in enumerate(all_para_individual):
        q_input.put((cur_result_num, para,))

    q_output = mp.Queue()

    workers = [mp.Process(target=func_worker, args=(func_run, para_share, q_input, q_output))
               for _ in range(threads)]

    for w in workers:
        w.start()

    temp_result = {}
    final_result = None
    cur_processing_num = 0
    total_item_num = len(all_para_individual)
    while cur_processing_num < total_item_num:
        cur_result_num, cur_result = q_output.get()
        temp_result[cur_result_num] = cur_result

        while cur_processing_num in temp_result:
            final_result = func_merge(final_result, temp_result.pop(cur_processing_num))
            cur_processing_num += 1

    for w in workers:
        q_input.put(None)

    for w in workers:
        w.join()
    return final_result


def run_multiple_process_big_list(func_add, func_run, func_merge, func_worker=None,
                                  para_add=(),
                                  para_share=None, threads=1):
    if func_worker is None:
        func_worker = _func_worker_no_auto_stop

    q_input = mp.Queue()
    q_output = mp.Queue()
    q_max_item_in_queue = threads * 100
    workers = [mp.Process(target=func_worker, args=(func_run, para_share, q_input, q_output))
               for _ in range(threads)]

    for w in workers:
        w.start()

    temp_result = {}
    final_result = None
    cur_output_num = 0
    cur_input_num = 0
    is_all_added_to_q = False
    while True:
        if (q_output.qsize() < q_max_item_in_queue) and \
                (q_input.qsize() < q_max_item_in_queue) \
                and (not is_all_added_to_q):
            cur_para = next(func_add(*para_add))
            if cur_para is not None:
                q_input.put((cur_input_num, cur_para,))
                cur_input_num += 1
            else:
                is_all_added_to_q = True

        cur_result_num, cur_result = q_output.get()
        temp_result[cur_result_num] = cur_result

        while cur_output_num in temp_result:
            final_result = func_merge(final_result, temp_result.pop(cur_output_num))
            cur_output_num += 1

        if is_all_added_to_q and cur_output_num == cur_input_num:
            break

    for w in workers:
        q_input.put(None)

    for w in workers:
        w.join()
    return final_result


def run_function(func_run, func_para, threads_type=1, func_timeout=None, **kwargs):
    if threads_type == 1:
        all_result = []
        for para in func_para:
            result = func_run(*para)
            if result is not None:
                all_result.append(result)
        return all_result
    elif threads_type == 2:
        if func_timeout is None:
            return _run_multiple_process(func_run, func_para, **kwargs)
        else:
            return _run_multiple_thread_time_out(func_run, func_para, func_timeout, **kwargs)
    elif threads_type == 3:
        return _run_multiple_process_simple(func_run, func_para, **kwargs)


def mp_raw_array_data(data, array_c_type=None):
    dim = data.shape
    num = reduce(lambda x, y: x * y, dim)
    # Note: data.dtype.char may be wrong.
    if array_c_type is None:
        array_c_type = data.dtype.char
    base = mp.Array(array_c_type, num, lock=False)
    np_array = np.frombuffer(base, dtype=data.dtype)
    np_array = np_array.reshape(dim)
    np_array[:] = data
    return np_array


class MPRunner:
    def __init__(self, func_run, func_merge=None, func_worker=None,
                 para_share=None, para_merge=(), copy_shared_para=False,
                 threads=1, max_job_in_queue=1000):
        if threads is None:
            threads = 1
        if func_merge is None:
            def func_merge(f_final_result, f_cur_result):
                if f_final_result is None:
                    f_final_result = [f_cur_result]
                else:
                    f_final_result.append(f_cur_result)
                return f_final_result
        if func_worker is None:
            func_worker = _func_worker_no_auto_stop

        self._func_merge = func_merge
        self._func_run = func_run

        self._para_merge = para_merge
        self._para_share = para_share

        self._q_input = mp.Queue()
        self._q_output = mp.Queue()
        self._q_max_item_in_queue = threads * max_job_in_queue

        self._temp_result = {}
        self._final_result = None

        self._total_output_num = 0
        self._total_input_num = 0

        self._workers = [mp.Process(target=func_worker,
                                    args=(func_run, para_share, self._q_input, self._q_output, copy_shared_para))
                         for _ in range(threads)]

        for w in self._workers:
            w.start()

    def add_parameter_for_job(self, cur_para, debug=0):
        if debug == 1:
            if self._para_share is None:
                return self._func_run(*cur_para)
            else:
                return self._func_run(*cur_para, *self._para_share)

        if (self._q_output.qsize() > self._q_max_item_in_queue) or \
                (self._q_input.qsize() > self._q_max_item_in_queue):
            cur_result_num, cur_result = self._q_output.get()
            self._temp_result[cur_result_num] = cur_result

            while self._total_output_num in self._temp_result:
                self._final_result = self._func_merge(
                    self._final_result, self._temp_result.pop(self._total_output_num), *self._para_merge)
                self._total_output_num += 1

        self._q_input.put((self._total_input_num, cur_para,))
        self._total_input_num += 1

    def get_result(self):
        for _ in self._workers:
            self._q_input.put(None)

        while self._total_output_num < self._total_input_num:
            cur_result_num, cur_result = self._q_output.get()
            self._temp_result[cur_result_num] = cur_result

            while self._total_output_num in self._temp_result:
                self._final_result = self._func_merge(
                    self._final_result, self._temp_result.pop(self._total_output_num), *self._para_merge)
                self._total_output_num += 1

        for w in self._workers:
            w.join()
        return self._final_result
