#class that describes memory block object
class Block:
    def __init__(self, block_id:int, size:int):
        self.id = block_id
        self.size = size
        self.busy = False
        self.fragmentation = 0
        self.job_ID=None
#class that describes job object
class Job:
    def __init__(self, job_id:int, size:int, time_needed:int):
        self.jobId = job_id
        self.jobSize = size
        self.timeNeeded = time_needed
        self.timeTaken = 0
        self.block_ID=None
        self.timeQueuing=0

#Class that describes waiting queue for jobs that do not have a suitable memory block
class Queue:
    def __init__(self):
        self.queue:list[Job] = []
    
    #This function adds a job to the queue
    def add_job(self, job:Job):
        self.queue.append(job)
    
    #This function removes a job with a specifc index from the queue
    def remove_job(self,idx):
        #The function does this by checking to see if the queue is empty before poping
        if len(self.queue) > 0:
            self.queue.pop(idx)
        else:
            print("Queue is empty")

    #this function updates the waiting time fir the jobs in the queue
    def update_time_waiting(self):
        for q_job in self.queue:
            q_job.timeQueuing+=1

class Memory:
    def __init__(self, m_list:list[Block]):
        self.memory_list = m_list #this is an array of Block objects
        self.waiting_queue = Queue()
        self.busy_list:list[Job] = []
        self.completed_jobs:list[Job] = []

    #This function input a job into the memory using best fit
    def input_job(self,job:Job):

        temp=[]#this is a list to store the memory block that can hold the incoming job
        current_idx=0 #this is to store the index of the block we are on
        fitting_idx=[]#this holds the index of the memory blocks in temp
        
        #Loop to go through all the blocks in Memor List
        for block in self.memory_list:
            
            #Thus checks if the block is empty
            if block.busy == False:
                #Then get the difference between the memory space and job size
                diff= block.size-job.jobSize

                #If the space can hold the job the difference is added to the temp variable
                #And its index added to the fitting index variable
                if diff>0:
                    temp.append(diff)
                    fitting_idx.append(current_idx)
            current_idx+=1    

        #If there is no block that can hold if we exit and return False
        if len(temp)==0:
            self.waiting_queue.add_job(job)
            print("There are no memory blocks available for Job"+job.jobId)   
            return False
        
        #Else we find the lowest fragmentation in the temp variable and its index
        #Then we assign the job to it
        else:         
            target=min(temp)
            target_idx=fitting_idx[temp.index(target)]
            self.memory_list[target_idx].busy=True;
            self.memory_list[target_idx].job_ID=job.jobId
            self.memory_list[target_idx].fragmentation=target
            return True
    
    #This function is for the busy list it increases the time on the jobs in it
    def process_jobs(self):
        a=0
        for p_job in self.busy_list:
            p_job.timeTaken+=1

            #This also checks if the jobs has been fully processed 
            #If so it removes it from the busy and deallocated the memory block
            if p_job.timeTaken==p_job.timeNeeded:
                self.completed_jobs.append(self.busy_list.pop(a))
                for block in self.memory_list:
                    if p_job.block_ID==block.id:
                        block.fragmentation=0
                        block.busy=False
                        block.job_ID=None
                        break
            a+=1
    
    #This function is for the processes that occur when the clock ticks
    def tick(self,new_job:Job):
        #We first run process_jobs to update times and remove finished jobs
        self.process_jobs()

        #Then we update times for the queuing jobs
        self.waiting_queue.update_time_waiting
        #We then add the incoming jobs to the queue 
        self.waiting_queue.add_job(new_job)

        job_num=-1
        # To process the jobs we use a for loop to find the oldest job
        #that can be accepted into the memory list and insert it
        for job in self.waiting_queue:
            job_idx+=0
            job_accepted=self.input_job(job)

            #if the job has been accepted the loop breaks
            if job_accepted==True:
                self.waiting_queue.remove_job(job_idx)
                break

