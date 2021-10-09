import multiprocessing as mp
import copy


class WorkerBase:
    def __init__(self, worker_id, func, func_para_share, q_input, q_output):
        self.worker_id = worker_id
        self.q_input = q_input
        self.q_output = q_output
        self.func_para_share = func_para_share
        self.func = func

    def run(self, *para):
        return self.func(*para)

    def daemon_run(self):
        """
        Run the jobs
        :return: 0 - job success; 1 - Get End command
        """
        q_item = self.q_input.get(block=True)
        if q_item is None:
            return 1

        job_id, para = q_item
        try:
            if self.func_para_share is not None:
                para += self.func_para_share
            result = self.run(*para)
        except Exception as e:
            result = None
            print(para, e)
        self.q_output.put((job_id, self.worker_id, result))
        return 0


def _worker_run(workers: list):
    continue_run = 1
    while continue_run:
        for worker in workers:
            worker_result = worker.daemon_run()
            if worker_result == 1:
                continue_run = 0
                break


class MPRunnerForDistributedWorker:
    def __init__(self, func_run, Worker=None, para_distribute=None, threads=None):
        if threads is None:
            threads = 1
        if Worker is None:
            Worker = WorkerBase

        self._q_input = []
        self._q_output = mp.Queue()

        # Generate cur worker
        worker_in_subprocesses = [[] for _ in range(threads)]
        for worker_id, p_dist in enumerate(para_distribute):
            q_input = mp.Queue()
            self._q_input.append(q_input)
            worker_cur = Worker(worker_id, func_run, p_dist, q_input, self._q_output)
            cur_p = worker_id % threads
            worker_in_subprocesses[cur_p].append(worker_cur)

        self._subprocesses = [mp.Process(target=_worker_run, args=(w,)) for w in worker_in_subprocesses]

        for p in self._subprocesses:
            p.start()

    def run_job(self, para_job):
        for q in self._q_input:
            q.put((0, para_job,))

        job_num = len(self._q_input)
        result = [None for _ in range(job_num)]

        for _ in range(job_num):
            job_id, worker_id, cur_result = self._q_output.get()
            result[worker_id] = cur_result
        return result

    def stop(self):
        for q in self._q_input:
            q.put(None)

        for w in self._subprocesses:
            w.join()


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


class MPRunner:
    def __init__(self, func_run, func_merge=None, func_worker=None,
                 para_share=None, para_merge=(), copy_shared_para=False,
                 threads=1, max_job_in_queue=None):
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
        if max_job_in_queue is None:
            self._q_max_item_in_queue = None
        else:
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

        if self._q_max_item_in_queue is not None:
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
