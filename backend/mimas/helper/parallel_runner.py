import ray
import logging
import ray.util.queue
import time
from multiprocessing import Process, Queue
import copy


def worker(queue_jobs, queue_results, para_shared):
    para_own = copy.deepcopy(para_shared)
    while 1:
        job = queue_jobs.get()

        # print(job)
        if job is None:
            queue_results.put(None)
            break
        job_id, (function, para) = job
        if isinstance(para, dict):
            result = function(**para, **para_own)
        else:
            result = function(*para, **para_own)
        queue_results.put((job_id, result))


class MPRunner:
    def __init__(self, n_processes=1, para_shared={}):
        self._queue_jobs = Queue()
        self._queue_results = Queue()

        self._job_pool = [Process(target=worker, args=(self._queue_jobs, self._queue_results, para_shared))
                          for _ in range(n_processes)]
        [x.start() for x in self._job_pool]
        self._job_id = 0
        self._para_shared = para_shared

    def add_job(self, function, parameters, debug=0):
        if debug:
            return function(*parameters, **self._para_shared)
        else:
            self._job_id += 1
            self._queue_jobs.put((self._job_id, (function, parameters)))
            return self._job_id

    def get_result(self):
        n_worker = 0
        for _ in range(len(self._job_pool)):
            self._queue_jobs.put(None)
            n_worker += 1

        result_all = []
        while n_worker > 0:
            result = self._queue_results.get()
            if result is None:
                n_worker -= 1
                continue
            result_all.append(result)

            # if len(result_all) % 10000 == 0:
            #    print(len(result_all))

        [x.join() for x in self._job_pool]

        result_all.sort(key=lambda x: x[0])
        result_all = [x[1] for x in result_all]
        return result_all


def r(x, y):
    print(x, y)
    return x + 1


if __name__ == '__main__':
    parallel = MPRunner(n_processes=5, para_shared={"y": 2})
    for i in range(10):
        parallel.add_job(r, (100 + i,))

    print(parallel.get_result())


@ray.remote
def run_in_cluster(function, parameters):
    try:
        function(*parameters)
    except Exception as e:
        print(("Error :{}\nFunction: {}\nParameters: {}".format(str(e), str(function), str(parameters))))


@ray.remote
def run_in_cluster_with_shared_parameters(function, parameters, shared_parameters):
    try:
        function(*parameters, *shared_parameters)
    except Exception as e:
        print(("Error :{}\nFunction: {}\nParameters: {}\n Shared parameters".format(
            str(e), str(function), str(parameters), str(shared_parameters))))


class ParallelRunnerSimple:
    def __init__(self, n_processes=None, temp_dir: str = None):
        ray.init(num_cpus=n_processes, _temp_dir=temp_dir)
        print(ray.cluster_resources())
        self._job_pool = []
        self._n_processes = n_processes

    def __del__(self):
        [ray.get(job) for job in self._job_pool]

    def add_job(self, function, parameters, debug=0):
        if debug == 1:
            return function(*parameters)
        else:
            job_id = run_in_cluster.remote(function, parameters)
            self._job_pool.append(job_id)
            return job_id

    def get_result(self):
        result = []
        for job in self._job_pool:
            result.append(ray.get(job))
        self._job_pool = []
        return result


@ray.remote
class Worker:
    def __init__(self, queue_work, queue_result):
        self._para = {}
        self._queue_work = queue_work
        self._queue_result = queue_result

    def run(self):
        while 1:
            data = self._queue_work.get()
            # If got STOP signal.
            if data is None:
                self._para = {}
                self._queue_result.put(None)
                return

            # print(data)
            job_id, (function_id, parameters_id) = data
            parameters = []

            if function_id in self._para:
                # print("fid1", function_id)
                function = self._para[function_id]
                for p in parameters_id:
                    if p in self._para:
                        parameters.append(self._para[p])
                    else:
                        p_obj = ray.get(p)
                        self._para[p] = p_obj
                        parameters.append(p_obj)
                        # print("-> Get ", p)
            else:
                # print("fid2", function_id)
                function = ray.get(function_id)
                self._para[function_id] = function
                for p in parameters_id:
                    p_obj = ray.get(p)
                    self._para[p] = p_obj
                    parameters.append(p_obj)

            result = function(*parameters)

            result_data = (job_id, result)
            # print("**", result_data)
            self._queue_result.put(result_data)


class ParallelRunner:
    def __init__(self, n_processes=None, temp_dir: str = None):
        ray.init(num_cpus=n_processes, _temp_dir=temp_dir)
        self._queue_work = ray.util.queue.Queue()
        self._queue_result = ray.util.queue.Queue()

        print(ray.cluster_resources())
        self._job_pool = [Worker.remote(self._queue_work, self._queue_result) for _ in range(n_processes)]
        [x.run.remote() for x in self._job_pool]
        self._n_processes = n_processes

        self._ray_parameter_id = {}
        self._ray_function_id = {}
        self._function_id = {}
        self._function_job_id = {}

    def __del__(self):
        self.exit()

    def exit(self):
        for _ in self._job_pool:
            self._queue_work.put(None)

    def add_job(self, function, parameters, debug=0):
        if debug == 1:
            return function(*parameters)
        else:
            function_id = id(function)
            if function_id not in self._function_id:
                self._function_id[function_id] = len(self._function_id)
                self._function_job_id[self._function_id[function_id]] = 0
                function_ray_id = ray.put(function)
                self._ray_function_id[function_id] = function_ray_id

            parameters_ray_id = []

            if self._ray_parameter_id:
                for p in parameters:
                    if id(p) not in self._ray_parameter_id:
                        parameters_ray_id.append(ray.put(p))
                    else:
                        parameters_ray_id.append(self._ray_parameter_id[id(p)])
            else:
                for p in parameters:
                    ray_id = ray.put(p)
                    parameters_ray_id.append(ray_id)
                    self._ray_parameter_id[id(p)] = ray_id

            work_data = (self._function_id[function_id], self._function_job_id[self._function_id[function_id]]), \
                        (self._ray_function_id[function_id], parameters_ray_id)
            self._queue_work.put(work_data)
            self._function_job_id[self._function_id[function_id]] += 1

    def get_result(self):
        result = {}
        # Put STOP signal
        stop_n = 0
        for _ in self._job_pool:
            self._queue_work.put(None)
            stop_n += 1

        # Get result
        while stop_n > 0:
            result_from_queue = self._queue_result.get()
            if result_from_queue is None:
                stop_n -= 1
                continue
            (function_id, job_id), result_cur = result_from_queue
            if function_id in result:
                result[function_id].append((job_id, result_cur))
            else:
                result[function_id] = [(job_id, result_cur)]

        # Clean result
        for function_id in result:
            r = result[function_id]
            r.sort(key=lambda x: x[0])
            result[function_id] = [x[1] for x in r]

        [x.run.remote() for x in self._job_pool]

        if len(result) == 1:
            for function_id in result:
                return result[function_id]
        else:
            return result
