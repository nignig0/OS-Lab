import threading
import time
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from classes import *    # Your block and job classes
from constants import *  # MEMORY_LIST, JOBLIST, etc.

def make_use_of_block(block, job, free_list, busy_list, lock):
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

def first_fit(lock):
    free_list = set(MEMORY_LIST)
    busy_list = set()
    threads = []

    block_usage_map = {block: 0 for block in MEMORY_LIST}

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
                    thread = threading.Thread(target=make_use_of_block, args=(block, job, free_list, busy_list, lock))
                    job.in_progress = True
                    block_usage_map[block] += 1
                    thread.start()
                    threads.append(thread)
                    break
        if not any([not job.done for job in JOBLIST]):
            break

    for t in threads:
        t.join()

    for block, usage in block_usage_map.items():
        print(f"block #{block.index}: {usage}")

if __name__ == "__main__":
    lock = threading.Lock()

    x = np.arange(1, len(MEMORY_LIST)+ 1)
    target_heights = np.array([memory.space for memory in MEMORY_LIST])
    current_heights = np.zeros_like(target_heights)

    fig, ax = plt.subplots()
    ax.set_ylim(0, max(target_heights) + 100)
    ax.set_xticks(x)
    ax.set_xticklabels(x)

    bar_outline = ax.bar(x, target_heights, fill=False, edgecolor='black', linewidth=2)
    fill_bars = ax.bar(x, current_heights, color='blue', zorder=2)

    bar_states = {
        block.index: {
            'current_target': 0,
            'actual_target': 0,
            'transitioning': False
        }

        for block in MEMORY_LIST
    }
    def update(frame):
        with lock:
            for i, block in enumerate(MEMORY_LIST):
                current = fill_bars[i].get_height()
                state = bar_states[block.index]
                # If block is busy, get job size, else 0
                target = 0 if block.job_in_progress is None else JOBLIST[block.job_in_progress - 1].size

                if target != state['actual_target']:
                    state['actual_target'] = target
                    state['transitioning'] = True

                if state['transitioning']:
                    if current > 0:
                        new_height = max(current - 500, 0)
                        fill_bars[i].set_height(new_height)
                    else:
                        state['transitioning'] = False 
                
                else:

                    if current < target:
                        new_height = min(current + 500, target)
                        fill_bars[i].set_height(new_height)
                    else:
                    
                        new_height = max(current - 500, target)
                        fill_bars[i].set_height(new_height)
        return fill_bars

    ani = FuncAnimation(fig, update, interval=50, blit=False)

    # Run first_fit in a separate thread
    threading.Thread(target=first_fit, args=(lock,), daemon=True).start()

    plt.show()
