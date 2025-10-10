import time

class MemoryBlock:
    def __init__(self, index, space, job_in_progress = None):
        self.space = space
        self.index = index
        self.job_in_progress = job_in_progress

class Job:
    def __init__(self, job_stream_number, time, size, in_progress = False, done = False, time_till_memory_block = time.time()):
        self.time = time
        self.size = size
        self.done = done
        self.in_progress = in_progress
        self.job_stream_number = job_stream_number
        self.time_till_memory_block = time_till_memory_block