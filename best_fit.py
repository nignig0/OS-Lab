import threading
import time
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from classes import MemoryBlock, Job
from constants import MEMORY_LIST, JOBLIST

def make_use_of_block(block, job, free_list, busy_list, lock):
    """Allocate a job to a memory block and execute it."""
    with lock:
        busy_list.add(block)
        free_list.remove(block)
        block.job_in_progress = job.job_stream_number
        print(f"Job #{job.job_stream_number} in progress!")
        print(f"Job #{job.job_stream_number} is using block #{block.index}")
    
    time.sleep(job.time)

    with lock:
        free_list.add(block)
        busy_list.remove(block)
        job.done = True
        block.job_in_progress = None
        print(f"Job #{job.job_stream_number} complete!")

def best_fit(lock):
    """Best-fit memory allocation algorithm"""
    free_list = set(MEMORY_LIST)
    busy_list = set()
    threads = []

    # Track statistics
    block_usage_map = {block: 0 for block in MEMORY_LIST}
    wait_queue = []
    job_wait_times = {}
    job_completion_times = {}

    start_time = time.time()

    while True:
        current_time = time.time() - start_time

        # Process all jobs (including jobs in wait queue)
        for job in JOBLIST + wait_queue:
            if job.done or job.in_progress:
                continue

            # Check if job size exceeds the max available block size
            if job.size > max([memory.space for memory in MEMORY_LIST]):
                print(f"Not enough space for job #{job.job_stream_number}")
                job.done = True
                continue

            # Track waiting time
            if job not in wait_queue and job.job_stream_number not in job_wait_times:
                job_wait_times[job.job_stream_number] = current_time
            
            # Find the best-fit block
            best_block = None
            min_waste = float('inf')

            with lock:
                available_blocks = [block for block in free_list if block.space >= job.size]

                # Find the block with the minimum waste
                if available_blocks:
                    for block in available_blocks:
                        waste = block.space - job.size
                        if waste < min_waste:
                            min_waste = waste
                            best_block = block

            if best_block:
                # Remove from wait queue if it was waiting
                if job in wait_queue:
                    wait_queue.remove(job)
                    wait_time = current_time - job_wait_times[job.job_stream_number]
                    print(f"Job #{job.job_stream_number} waited for {wait_time:.2f} seconds")
                
                thread = threading.Thread(
                    target=make_use_of_block,
                    args=(best_block, job, free_list, busy_list, lock)
                )
                job.in_progress = True
                block_usage_map[best_block] += 1
                thread.start()
                threads.append(thread)
            else:
                if job not in wait_queue and job in JOBLIST:
                    wait_queue.append(job)
        
        if all(job.done for job in JOBLIST):
            break

        time.sleep(0.1)
    
    for t in threads:
        t.join()
    
