import threading
import time
from constants import MEMORY_LIST, JOBLIST

def make_use_of_block(block, job, free_list, busy_list, lock, fragementation_list):
    with lock:
        busy_list.add(block)
        free_list.remove(block)
        block.job_in_progress = job.job_stream_number
        print(f"Job #{job.job_stream_number} in progress!")
        print(f"Job #{job.job_stream_number} is using block #{block.index}")
        fragementation_list[job] = block.space - job.size
        job.time_till_memory_block = time.time() - job.time_till_memory_block


    time.sleep(job.time) # Simulate job processing time

    with lock:
        free_list.add(block)
        busy_list.remove(block)
        job.done = True
        block.job_in_progress = None
        print(f"Job #{job.job_stream_number} complete!")

def first_fit(lock):
    MEMORY_LIST.sort(key=lambda x: x.space)
    #uncomment if you want to run best fit
    free_list = set(MEMORY_LIST)
    busy_list = set()
    threads = []
    start_time = time.time()

    block_usage_map = {block: 0 for block in MEMORY_LIST}
    fragmentation_list = {job: 0 for job in JOBLIST}

    while True:
        
        for job in JOBLIST:
            if job.done or job.in_progress:
                continue
            if job.size > max([memory.space for memory in MEMORY_LIST]):
                print(f"Not enough space for job #{job.job_stream_number}")
                job.done = True
                continue
            for block in MEMORY_LIST:
                can_allocate = False
                with lock:
                    can_allocate = block in free_list and block.space >= job.size
                if can_allocate:
                    thread = threading.Thread(target=make_use_of_block, args=(block, job, free_list, busy_list, lock, fragmentation_list))
                    job.in_progress = True
                    block_usage_map[block] += 1
                    thread.start()
                    threads.append(thread)
                    break
        if not any([not job.done for job in JOBLIST]):
            break
    with lock:
        print(f"Waiting queue length = {len(JOBLIST) - len(busy_list)}")
    for t in threads:
        t.join()

    for block, usage in block_usage_map.items():
        print(f"block #{block.index}: {usage}")
    for job, fragementation in fragmentation_list.items():
        print(f"Job number = {job.job_stream_number}, fragmentation caused = {fragementation}, waiting_time = {job.time_till_memory_block}")
    end_time = time.time()
    print(f"Time taken: {end_time - start_time}")