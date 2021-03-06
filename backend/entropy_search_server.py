import sys
import multiprocessing
from multiprocessing import Process
from multiprocessing.queues import Queue
import traceback

from entropy_search_terminal import main as entropy_search_main


def run_function_with_output_to_queue(func, args, queue):
    stdout = sys.stdout
    sys.stdout = queue
    try:
        func(*args)
    except Exception as e:
        print(traceback.format_exc())
        print(e)
    sys.stdout = stdout


class StdoutQueue(Queue):
    def __init__(self, *args, **kwargs):
        ctx = multiprocessing.get_context()
        super(StdoutQueue, self).__init__(*args, **kwargs, ctx=ctx)

    def write(self, msg):
        self.put(msg)

    def flush(self):
        sys.__stdout__.flush()


class EntropySearchServer:
    def __init__(self):
        self.output_queue = StdoutQueue()
        self.output_str = []
        self.thread = None

    def start_search(self, para):
        self.output_str = []
        para.update({
            "method": "untarget-identity",
            "clean_spectra": True,
        })
        if self.thread is not None:
            self.thread.join()
        self.thread = Process(target=run_function_with_output_to_queue,
                              args=(entropy_search_main, (para,), self.output_queue))
        self.thread.start()
        return

    def get_output(self):
        try:
            while not self.output_queue.empty():
                output_str = self.output_queue.get_nowait()
                print(output_str)
                if output_str is not None:
                    self.output_str.append(output_str)
        except AttributeError as e:
            pass
        return "".join(self.output_str)

    def stop(self):
        self.thread.terminate()
        # self.thread.join()
        return self.get_output()

    def is_finished(self):
        self.get_output()
        if self.thread is None:
            return True
        else:
            if self.thread.pid is None:
                return False
            self.thread.join(0.1)
            if self.thread.exitcode is None:
                return False
            else:
                return True
