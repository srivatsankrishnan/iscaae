from envlogger import reader

log_dir = "/n/holylabs/LABS/janapa_reddi_lab/Lab/skrishnan/workspace/arch-gym/sims/Sniper/envlogger"

with reader.Reader(
    data_directory = log_dir) as r:
    for episode in r.episodes:
        for step in episode:
            print(step)