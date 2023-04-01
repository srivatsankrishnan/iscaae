import random


# Constants
RANDOM = "sims/DRAM/DRAMSys/library/resources/traces/random.stl"
STREAM = "sims/DRAM/DRAMSys/library/resources/traces/stream.stl"
CLOUD  = "sims/DRAM/DRAMSys/library/resources/traces/cloud-1.stl"
LEN = 10000
SEED = 0


# Setup
random.seed(SEED)
f1 = open(RANDOM, "r")
f2 = open(STREAM, "r")
read_files = [f1, f2]
write_file = open(CLOUD, "w")
line_num = 0


# Randomly generate new cloud workload file 
while line_num < LEN:
    read_file = random.choice(read_files)
    for i in range(50):
        trace_line = read_file.readline().split(":")[1]
        updated_line = str(line_num) + ":\t" + trace_line[1:]
        write_file.write(updated_line)
        line_num += 1


# Close files
f1.close()
f2.close()
write_file.close()
