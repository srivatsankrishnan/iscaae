import os
import sys
import json
import random
import math
import configparser
import numpy as np
import yaml
os.sys.path.insert(0, os.path.abspath('/../../configs'))

#from configs import configs
from configs import arch_gym_configs
import shutil
from subprocess import Popen, PIPE
import pandas as pd
from math import ceil

class CustomListDumper(yaml.Dumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        return super(CustomListDumper, self).increase_indent(flow, False)


class helpers():
    def __init__(self):
        self.mem_control_basepath = arch_gym_configs.dram_mem_controller_config
        self.sniper_basepath = arch_gym_configs.sniper_config
        #self.timeloop_param_obj = TimeloopConfigParams(arch_gym_configs.timeloop_parameters)
    
    def action_mapper(self, action, param):
        """
        RL agent outputs actions in [0,1]

        This function maps the action space to the actual values
        we split the action space (0,1) into equal parts depending on the number of valid actions each parameter can take
        We then bin the action to the appropriate range
        """
        num_bins = len(param)
        action_bin = 2/num_bins
        
        # create boundries for each bin
        boundries = np.arange(-1, 1, action_bin)
        
        
        # find the index in the boundries array that the action falls in
        try:
            action_index = np.where(boundries <= round(action))[0][-1]
        except Exception as e:
            print(action)
      
        return action_index
    def action_decoder_rl(self, act_encoded, rl_form):
        """
        Decode the action space for the RL agent
        """
        print("[Action Encoded]", act_encoded)
        act_decoded = {}
        
        # simle Encoding for string action space for memory controller
        page_policy_mapper = {0:"Open", 1:"OpenAdaptive", 2:"Closed", 3:"ClosedAdaptive"}
        scheduler_mapper = {0:"Fifo", 1:"FrFcfsGrp", 2:"FrFcfs"}
        schedulerbuffer_mapper = {0:"Bankwise", 1:"ReadWrite", 2:"Shared"}
        request_buffer_size_mapper = {0:1, 1:2, 2:4, 3:8, 4:16, 5:32, 6:64, 7:128}
        respqueue_mapper = {0:"Fifo", 1:"Reorder"}
        refreshpolicy_mapper = {0:"NoRefresh", 1:"AllBank"}
        refreshmaxpostponed_mapper = {0:1, 1:2, 2:4, 3:8}
        refreshmaxpulledin_mapper = {0:1, 1:2, 2:4, 3:8}
        arbiter_mapper = {0:"Simple", 1:"Fifo", 2:"Reorder"}
        max_active_transactions_mapper = {0:1, 1:2, 2:4, 3:8, 4:16, 5:32, 6:64, 7:128}

        if(rl_form == 'sa' or rl_form == 'macme_continuous'):
            act_decoded["PagePolicy"] =  page_policy_mapper[self.action_mapper(act_encoded[0], page_policy_mapper)]
            act_decoded["Scheduler"]  =  scheduler_mapper[self.action_mapper(act_encoded[1], scheduler_mapper)]
            act_decoded["SchedulerBuffer"]  =  schedulerbuffer_mapper[self.action_mapper(act_encoded[2], schedulerbuffer_mapper)]
            act_decoded["RequestBufferSize"]  =  request_buffer_size_mapper[self.action_mapper(act_encoded[3], 
                                                                                        request_buffer_size_mapper)]
            act_decoded["RespQueue"]  =  respqueue_mapper[self.action_mapper(act_encoded[4], respqueue_mapper)]
            act_decoded["RefreshPolicy"]  =  refreshpolicy_mapper[self.action_mapper(act_encoded[5], refreshpolicy_mapper)]
            act_decoded["RefreshMaxPostponed"]  =  refreshmaxpostponed_mapper[self.action_mapper(act_encoded[6],
                                                                                        refreshmaxpostponed_mapper)]
            act_decoded["RefreshMaxPulledin"]  =  refreshmaxpulledin_mapper[self.action_mapper(act_encoded[7], 
                                                                                            refreshmaxpulledin_mapper)]
            act_decoded["Arbiter"] =  arbiter_mapper[self.action_mapper(act_encoded[8], arbiter_mapper)]
            act_decoded["MaxActiveTransactions"] =  max_active_transactions_mapper[self.action_mapper(act_encoded[9],
                                                                                    max_active_transactions_mapper)]
        elif (rl_form == 'macme'):
            print("[Action Decoder]", act_encoded)
            
            act_decoded["PagePolicy"] =  page_policy_mapper[act_encoded[0]]
            act_decoded["Scheduler"]  =  scheduler_mapper[act_encoded[1]]
            act_decoded["SchedulerBuffer"]  =  schedulerbuffer_mapper[act_encoded[2]]
            act_decoded["RequestBufferSize"]  =  request_buffer_size_mapper[act_encoded[3]]
            act_decoded["RespQueue"]  =  respqueue_mapper[act_encoded[4]]
            act_decoded["RefreshPolicy"]  =  refreshpolicy_mapper[act_encoded[5]]
            act_decoded["RefreshMaxPostponed"]  =  refreshmaxpostponed_mapper[act_encoded[6]]
            act_decoded["RefreshMaxPulledin"]  =  refreshmaxpulledin_mapper[act_encoded[7]]
            act_decoded["Arbiter"] =  arbiter_mapper[act_encoded[8]]
            act_decoded["MaxActiveTransactions"] =  max_active_transactions_mapper[act_encoded[9]]
        elif(rl_form == 'tdm'):
            print("[Action Decoder]", act_encoded)
            
            act_decoded["PagePolicy"] =  page_policy_mapper[np.clip(act_encoded[0], 0, len(page_policy_mapper)-1)]
            act_decoded["Scheduler"]  =  scheduler_mapper[np.clip(act_encoded[1], 0, len(scheduler_mapper)-1)]
            act_decoded["SchedulerBuffer"]  =  schedulerbuffer_mapper[np.clip(act_encoded[2], 0, len(schedulerbuffer_mapper)-1)]
            act_decoded["RequestBufferSize"]  =  request_buffer_size_mapper[np.clip(act_encoded[3], 0, len(request_buffer_size_mapper)-1)]
            act_decoded["RespQueue"]  =  respqueue_mapper[np.clip(act_encoded[4], 0, len(respqueue_mapper)-1)]
            act_decoded["RefreshPolicy"]  =  refreshpolicy_mapper[np.clip(act_encoded[5], 0, len(refreshpolicy_mapper)-1)]
            act_decoded["RefreshMaxPostponed"]  =  refreshmaxpostponed_mapper[np.clip(act_encoded[6], 0, len(refreshmaxpostponed_mapper)-1)]
            act_decoded["RefreshMaxPulledin"]  =  refreshmaxpulledin_mapper[np.clip(act_encoded[7], 0, len(refreshmaxpulledin_mapper)-1)]
            act_decoded["Arbiter"] =  arbiter_mapper[np.clip(act_encoded[8], 0, len(arbiter_mapper)-1)]
            act_decoded["MaxActiveTransactions"] =  max_active_transactions_mapper[np.clip(act_encoded[9], 0, len(max_active_transactions_mapper)-1)]
        else:
            print("Invalid RL form")
            sys.exit()
        print("[Action Decoder]", act_decoded)
        return act_decoded


    def action_decoder_ga(self, act_encoded):
        print(act_encoded)
        act_decoded = {}
         # simle Encoding for string action space for memory controller
        page_policy_mapper = {0:"Open", 1:"OpenAdaptive", 2:"Closed", 3:"ClosedAdaptive"}
        scheduler_mapper = {0:"Fifo", 1:"FrFcfsGrp", 2:"FrFcfs"}
        schedulerbuffer_mapper = {0:"Bankwise", 1:"ReadWrite", 2:"Shared"}
        respqueue_mapper = {0:"Fifo", 1:"Reorder"}
        refreshpolicy_mapper = {0:"NoRefresh", 1:"AllBank"}#, 2:"PerBank", 3:"SameBank"}
        arbiter_mapper = {0:"Simple", 1:"Fifo", 2:"Reorder"}
        
        act_decoded["PagePolicy"] =  page_policy_mapper[int(act_encoded[0])]
        act_decoded["Scheduler"]  =  scheduler_mapper[int(act_encoded[1])]
        act_decoded["SchedulerBuffer"]  =  schedulerbuffer_mapper[int(act_encoded[2])]
        act_decoded["RequestBufferSize"]  =  int(act_encoded[3])
        act_decoded["RespQueue"]  =  respqueue_mapper[int(act_encoded[4])]
        act_decoded["RefreshPolicy"]  =  refreshpolicy_mapper[int(act_encoded[5])]
        act_decoded["RefreshMaxPostponed"]  =  int(act_encoded[6])
        act_decoded["RefreshMaxPulledin"]  =  int(act_encoded[7])
        act_decoded["Arbiter"]  =  arbiter_mapper[int(act_encoded[8])]
        act_decoded["MaxActiveTransactions"]  =  int(act_encoded[9])

        return act_decoded


    def random_walk(self):
        '''
                configurations are ordered in this fashion

                keys = ["PagePolicy", "Scheduler", "SchedulerBuffer", "RequestBufferSize", 
                "CmdMux", "RespQueue", "RefreshPolicy", "RefreshMaxPostponed", 
                "RefreshMaxPulledin", "PowerDownPolicy", "Arbiter", "MaxActiveTransactions" ]
        '''

        pagepolicy = random.randint(0,3)
        scheduler = random.randint(0,2)
        schedulerbuffer = random.randint(0,2)
        reqest_buffer_size = random.randint(1,8)
        respqueue = random.randint(0,1)
        refreshpolicy = random.randint(0,1)
        refreshmaxpostponed = random.randint(1,8)
        refreshmaxpulledin = random.randint(1,8)
        powerdownpolicy = random.randint(0,2)
        arbiter = random.randint(0,2)
        maxactivetransactions = random.randint(1,128)
        #max_buffer_depth = 128
        
        #rand_idx = random.randint(1,math.log2(max_buffer_depth))
        #maxactivetransactions = int(pow(2,rand_idx))

        rand_actions = [pagepolicy, scheduler, schedulerbuffer, reqest_buffer_size,
                        respqueue, refreshpolicy, refreshmaxpostponed, 
                        refreshmaxpulledin, arbiter, maxactivetransactions]

        #rand_actions_decoded = self.action_decoder(rand_actions)

        return rand_actions
    
    def read_modify_write_dramsys(self, action):
        print("[envHelpers][Action]", action)
        op_success = False
        mem_ctrl_file = arch_gym_configs.dram_mem_controller_config_file
        
        try:
            with open (mem_ctrl_file, "r") as JsonFile:
                data = json.load(JsonFile)
                data['mcconfig']['PagePolicy'] = action['PagePolicy']
                data['mcconfig']['Scheduler'] = action['Scheduler']
                data['mcconfig']['SchedulerBuffer'] = action['SchedulerBuffer']
                data['mcconfig']['RequestBufferSize'] = action['RequestBufferSize']
                data['mcconfig']['RespQueue'] = action['RespQueue']
                data['mcconfig']['RefreshPolicy'] = action['RefreshPolicy']
                data['mcconfig']['RefreshMaxPostponed'] = action['RefreshMaxPostponed']
                data['mcconfig']['RefreshMaxPulledin'] = action['RefreshMaxPulledin']
                data['mcconfig']['Arbiter'] = action['Arbiter']
                data['mcconfig']['MaxActiveTransactions'] = action['MaxActiveTransactions']

                with open (mem_ctrl_file, "w") as JsonFile:
                    json.dump(data,JsonFile)
                op_success = True
        except Exception as e:
            print(str(e))
            op_success = False
        return op_success

    def writemem_ctrlr(self,action_dict):
        mem_ctrl_filename = arch_gym_configs.dram_mem_controller_config_file
        write_success = False
        full_path = os.path.join(self.mem_control_basepath,mem_ctrl_filename)
        mcconfig_dict = {}
        mcconfig_dict ["mcconfig"] = action_dict
        jsonString = json.dumps(mcconfig_dict)
        
        try:
            jsonFile = open(full_path, "w")
            jsonFile.write(jsonString)
            jsonFile.close()
            write_success = True
        except Exception as e:
            print(str(e))
            write_success = False

        return write_success
    
    def read_modify_write_sniper_config(self,action_dict, cfg):
        write_success = False
        parser = configparser.ConfigParser()
        parser.read(cfg)
        print(action_dict)
        parser.set("perf_model/core/interval_timer", "dispatch_width", str(action_dict["core_dispatch_width"]))
        parser.set("perf_model/core/interval_timer", "window_size", str(action_dict["core_window_size"]))
        parser.set("perf_model/core/rob_timer", "outstanding_loads",str(action_dict["core_outstanding_loads"]))
        parser.set("perf_model/core/rob_timer", "outstanding_stores", str(action_dict["core_outstanding_stores"]))
        parser.set("perf_model/core/rob_timer", "commit_width", str(action_dict["core_commit_width"]))
        parser.set("perf_model/core/rob_timer", "rs_entries", str(action_dict["core_rs_entries"]))
        parser.set("perf_model/l1_icache", "cache_size", str(action_dict["l1_icache_size"]))
        parser.set("perf_model/l1_dcache", "cache_size", str(action_dict["l1_dcache_size"]))
        parser.set("perf_model/l2_cache", "cache_size", str(action_dict["l2_cache_size"]))
        parser.set("perf_model/l3_cache", "cache_size", str(action_dict["l3_cache_size"]))
        try:
            with open(cfg,'w') as configfile:
                parser.write(configfile)
                write_success = True
        except Exception as e:
            print(str(e))
            write_success = False
        
        return write_success
    
    def create_agent_configs(self,agent_ids, cfg):
        
        shutil.copy(cfg, 'arch_gym_x86_agent_{}.cfg'.format(agent_ids))

        # return absolute paths to the config files
        return os.path.abspath('arch_gym_x86_agent_{}.cfg'.format(agent_ids))
    
    def decode_timeloop_action(self, action):
        '''Transforms action indexes to action dictionary yaml accepted by timeloop'''
        new_arch_params = self.timeloop_param_obj.get_arch_param_template()
        all_params = self.timeloop_param_obj.get_all_params()
        it = 0

        # Assuming ordered dict behavior (insertion order) in python 3.6+
        for param in all_params.keys():
            if isinstance(all_params[param], dict):
                for subparam in all_params[param].keys():
                    new_arch_params[param][subparam] = all_params[param][subparam][int(
                        action[it] - 1)]

                    # fix for block-size and word bits
                    if subparam == 'block-size':
                        if 'memory_width' in new_arch_params[param].keys():
                            new_arch_params[param]['memory_width'] = int(
                                new_arch_params[param]['block-size']) * int(new_arch_params[param]['word-bits'])
                        elif 'width' in new_arch_params[param].keys():
                            # fix for dummy buffer width parameter
                            new_arch_params[param]['width'] = int(
                                new_arch_params[param]['block-size']) * int(new_arch_params[param]['word-bits'])

                    it += 1
            else:
                new_arch_params[param] = all_params[param][int(action[it] - 1)]
                it += 1

        return new_arch_params

    
    def create_timeloop_dirs(self, agent_id, base_script_dir, base_output_dir, 
                             base_arch_dir):
        '''Creates the script, output and arch directories for a given agent_id for timeloop'''
        script_dir_agent = base_script_dir + "/" + str(agent_id)
        output_dir_agent = base_output_dir + "/" + str(agent_id)
        arch_dir_agent = base_arch_dir + "/" + str(agent_id)

        src_script_path = base_script_dir + "/run_timeloop.sh"
        arch_yaml_path = base_arch_dir + "/eyeriss_like.yaml"
        arch_comp_path = base_arch_dir + "/components"
        arch_dest_path = arch_dir_agent + "/components"

        os.makedirs(script_dir_agent, exist_ok=True)
        shutil.copy(src_script_path, script_dir_agent)
        os.makedirs(output_dir_agent, exist_ok=True)
        os.makedirs(arch_dir_agent, exist_ok=True)
        shutil.copy(arch_yaml_path, arch_dir_agent)
        shutil.copytree(arch_comp_path, arch_dest_path)

        return script_dir_agent, output_dir_agent, arch_dir_agent
    
    def remove_dirs(self, dirs):
        '''Removes a list of paths'''
        for path in dirs:
            shutil.rmtree(path)

    def compute_area_maestro(self, num_pe, l1_size, l2_size):
        MAC_AREA_MAESTRO=4470
        L2BUF_AREA_MAESTRO = 4161.536
        L1BUF_AREA_MAESTRO = 4505.1889
        L2BUF_UNIT = 32768
        L1BUF_UNIT = 64
        area = num_pe * MAC_AREA_MAESTRO + ceil(int(l2_size)/L2BUF_UNIT)*L2BUF_AREA_MAESTRO + ceil(int(l1_size)/L1BUF_UNIT)*L1BUF_AREA_MAESTRO * num_pe
        return area
    
    def reset(self):
        # if any csv and m files exists then remove the *.csv file and *.m files

        # get the file path
        file_path = os.path.dirname(os.path.realpath(__file__))
        print(file_path)
        results_file = os.path.join(file_path, self.mapping_file+".csv")
        mapping_file = os.path.join(file_path, self.mapping_file+".m")
        
        # clean up the results and mapping files
        if os.path.exists(results_file):
            print("csv file exists")
            os.remove(results_file)
        if os.path.exists(mapping_file):
            print("m file exists")
            os.remove(mapping_file)
        # return the initial state

        return np.zeros(self.observation_space.shape)

    def decode_cluster(self, idx):
        decoder = {0:'K', 1:'C', 2:'X', 3:'Y'}

        return decoder[idx]

    def decode_action_list(self, action):
        
        print("Action: {}".format(action))
        # convert all the values to int

        if len(action) == 1:
            action = [int(i) for i in action[-1]]
        else:
            action = [int(i) for i in action]
        # l2-S, l2-R, l2-K, l2-C, l2-X, l2-Y
        seed_l2 = action[0]
        seed_l1 = action[-2]
        if (action[-1]<=1):
            num_pe = 2
        else:
            num_pe = action[-1]
        print("Number of PE: {}".format(num_pe))
        print("P:", action)
        l1_df = [['S', action[2]], ['R', action[3]], ['K', action[4]], ['C', action[5]], ['X', action[6]], ['Y', action[7]]]
        

        l2_df = [['S', action[9]], 
            ['R', action[10]], 
            ['K', np.random.randint(1, action[4]) if action[4] > 1 else 1],
            ['C', np.random.randint(1, action[5]) if action[5] > 1 else 1],
            ['X', np.random.randint(1, action[6]) if action[6] > 1 else 1],
            ['Y', np.random.randint(1, action[7]) if action[7] > 1 else 1]]

        # permute the l1_df based on seed_l1
        np.random.seed(seed_l1)
        np.random.shuffle(l1_df)
        
        # permute the l2_df based on seed_l2
        np.random.seed(seed_l2)
        np.random.shuffle(l2_df)
        
        # convert l1_df to dictionary and l2_df to dictionary
        l1_dict = dict(l1_df)
        l2_dict = dict(l2_df)

        # get the cluster
        if (num_pe <= 1):
            num_pe = 2
            parallel_dim_l2 = [str(self.decode_cluster(action[8])), 1]
        else:
            parallel_dim_l2 = [str(self.decode_cluster(action[8])), np.random.randint(1, num_pe)]
        if (l2_dict[self.decode_cluster(action[1])] <= 1):
            print("Fix this!",l2_dict[self.decode_cluster(action[1])])
            parallel_dim_l1 = [str(self.decode_cluster(action[1])), 1]
        else:
            parallel_dim_l1 = [str(self.decode_cluster(action[1])), np.random.randint(1, l2_dict[self.decode_cluster(action[1])])]

        
        # append parallel_dim_l1 to l1_df at the beginning of the list
        l1_df.insert(0, parallel_dim_l1)
        l2_df.insert(0, parallel_dim_l2)

        
        final_df = l2_df + l1_df
        
        return final_df

    def get_dimensions(self, workload, layer_id):
        # add .csv to the workload name
        model_name = workload + ".csv"
        model_path = os.path.join(arch_gym_configs.mastero_model_path, model_name)
        
        # check if model_path exists
        if os.path.exists(model_path):
            print("model_path exists")
            import pandas as pd

            # Read in the csv file
            df = pd.read_csv(model_path)

            # Get user input for row number
            layer_id = layer_id

            # Select the row based on user input
            row = df.iloc[layer_id]

            # convert the row to dictionary
            row_dict = row.to_dict()

            # convert the dictionary to list
            row_list = list(row_dict.values())
            return row_dict, row_list

        else:
            print("model_path does not exist")
            sys.exit()

    def get_CONVtypeShape(self, dimensions, CONVtype=1):
        CONVtype_dicts = {0:"FC", 1:"CONV",2:"DSCONV", 3:"GEMM"}
        CONVtype = CONVtype_dicts[CONVtype]
        if CONVtype == "CONV"or CONVtype=="DSCONV":
            pass
        elif CONVtype == "GEMM" or CONVtype=="SGEMM":
            SzM, SzN, SzK,*a = dimensions
            dimensions = [SzN, SzK, SzM, 1, 1, 1]
        elif CONVtype == "FC":
            SzOut, SzIn, *a = dimensions
            dimensions = [SzOut, SzIn, 1, 1, 1, 1]
        else:
            print("Not supported layer.")
        return dimensions
    
    def write_maestro(self, indv=None, workload= None, layer_id= 0, m_file=None):
        _, dimension = self.get_dimensions(workload, layer_id)
        print("[DEBUG][write_maestro][dimension: {}]", dimension)
        
        m_type_dicts = {0:"CONV", 1:"CONV", 2:"DSCONV", 3:"CONV"}
        
        print("[DEBUG][write_maestro][m_file: {}]", m_file)
        dimensions = [dimension]
        with open("{}.m".format(m_file), "w") as fo:
            fo.write("Network {} {{\n".format(layer_id))
            for i in range(len(dimensions)):
                dimension = dimensions[i]
                m_type = m_type_dicts[int(dimension[-1])]
                dimension = self.get_CONVtypeShape(dimension, int(dimension[-1]))
                print(dimension)
                
                fo.write("Layer {} {{\n".format(m_type))
                fo.write("Type: {}\n".format(m_type))
                fo.write(
                    "Dimensions {{ K: {:.0f}, C: {:.0f}, Y: {:.0f}, X: {:.0f}, R: {:.0f}, S: {:.0f} }}\n".format(
                        *dimension))
                fo.write("Dataflow {\n")
                for k in range(0, len(indv), 7):
                    for i in range(k, k + 7):
                        if len(indv[i]) == 2:
                            d, d_sz = indv[i]
                        else:
                            d, d_sz, _ = indv[i]
                        if i % 7 == 0:
                            if k != 0:
                                fo.write("Cluster({},P);\n".format(d_sz))
                        else:
                            sp = "SpatialMap" if d == indv[k][0] or (
                                        len(indv[k]) > 2 and d == indv[k][2]) else "TemporalMap"
                            # MAESTRO cannot take K dimension as dataflow file
                            if not (m_type == "DSCONV"):
                                fo.write("{}({},{}) {};\n".format(sp, d_sz, d_sz, self.get_out_repr(d)))
                            else:
                                if self.get_out_repr(d) == "C" and self.get_out_repr(indv[k][0]) == "K":
                                    fo.write("{}({},{}) {};\n".format("SpatialMap", d_sz, d_sz, "C"))
                                else:
                                    if not (self.get_out_repr(d) == "K"):
                                        fo.write("{}({},{}) {};\n".format(sp, d_sz, d_sz, self.get_out_repr(d)))

                fo.write("}\n")
                fo.write("}\n")
            fo.write("}")

            # return the full path of the m_file
            return os.path.join(os.getcwd(), "{}.m".format(m_file))

    def get_out_repr(self, x):
        out_repr = set(["K", "C", "R", "S"])
        if x in out_repr:
            return x
        else:
            return x + "'"

    def run_maestro(self, exe, m_file, arch_configs):

        NocBW = arch_configs["NocBW"]
        offchipBW = arch_configs["offchipBW"]
        num_pe = arch_configs["num_pe"]
        l1_size = arch_configs["l1_size"]
        l2_size = arch_configs["l2_size"]
        num_pe = arch_configs["num_pe"]

        command = [exe,
           "--Mapping_file={}.m".format(m_file),
           "--full_buffer=false",
           "--noc_bw_cstr={}".format(NocBW),
           "--noc_hops=1",
           "--noc_hop_latency=1",
           "--offchip_bw_cstr={}".format(offchipBW),
           "--noc_mc_support=true",
           "--num_pes={}".format(int(num_pe)),
           "--num_simd_lanes=1",
           "--l1_size_cstr={}".format(l1_size),
           "--l2_size_cstr={}".format(l2_size),
           "--print_res=false",
           "--print_res_csv_file=true",
           "--print_log_file=false",
           "--print_design_space=false",
           "--msg_print_lv=0"]

        print(command)
        process = Popen(command, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        process.wait() 
        
        try:
            df = pd.read_csv("{}.csv".format(m_file))
            layer_name = df[" Layer Number"]
            runtime = np.array(df[" Runtime (Cycles)"]).reshape(-1, 1)
            runtime_series = np.array(df[" Runtime (Cycles)"]).reshape(-1, 1)
            throughput = np.array(df[" Throughput (MACs/Cycle)"]).reshape(-1, 1)
            energy = np.array(df[" Activity count-based Energy (nJ)"]).reshape(-1, 1)
            area = np.array(df[" Area"]).reshape(-1, 1)
            power = np.array(df[" Power"]).reshape(-1, 1)
            l1_size = np.array(df[" L1 SRAM Size Req (Bytes)"]).reshape(-1, 1)
            l2_size = np.array(df["  L2 SRAM Size Req (Bytes)"]).reshape(-1, 1)
            l1_size_series = np.array(df[" L1 SRAM Size Req (Bytes)"]).reshape(-1, 1)
            l2_size_series = np.array(df["  L2 SRAM Size Req (Bytes)"]).reshape(-1, 1)
            l1_input_read = np.array(df[" input l1 read"]).reshape(-1, 1)
            l1_input_write = np.array(df[" input l1 write"]).reshape(-1, 1)
            l1_weight_read = np.array(df["filter l1 read"]).reshape(-1, 1)
            l1_weight_write = np.array(df[" filter l1 write"]).reshape(-1, 1)
            l1_output_read = np.array(df["output l1 read"]).reshape(-1, 1)
            l1_output_write = np.array(df[" output l1 write"]).reshape(-1, 1)
            l2_input_read = np.array(df[" input l2 read"]).reshape(-1, 1)
            l2_input_write = np.array(df[" input l2 write"]).reshape(-1, 1)
            l2_weight_read = np.array(df[" filter l2 read"]).reshape(-1, 1)
            l2_weight_write = np.array(df[" filter l2 write"]).reshape(-1, 1)
            l2_output_read = np.array(df[" output l2 read"]).reshape(-1, 1)
            l2_output_write = np.array(df[" output l2 write"]).reshape(-1, 1)
            mac = np.array(df[" Num MACs"]).reshape(-1, 1)
            
            activity_count = {}
            activity_count["l1_input_read"] = l1_input_read
            activity_count["l1_input_write"] = l1_input_write
            activity_count["l1_weight_read"] = l1_weight_read
            activity_count["l1_weight_write"] = l1_weight_write
            activity_count["l1_output_read"] = l1_output_read
            activity_count["l1_output_write"] = l1_output_write
            activity_count["l2_input_read"] = l2_input_read
            activity_count["l2_input_write"] = l2_input_write
            activity_count["l2_weight_read"] = l2_weight_read
            activity_count["l2_weight_write"] = l2_weight_write
            activity_count["l2_output_read"] = l2_output_read
            activity_count["l2_output_write"] = l2_output_write
            activity_count["mac_activity"] = mac
            area = self.compute_area_maestro(num_pe, l1_size, l2_size)
            self.observation = [np.mean(x) for x in [runtime, throughput, energy, area, l1_size, l2_size, mac, power, num_pe]]
            
        except Exception as e:
            print(e)
            #set all the return values to -1
            runtime = np.array([1e20])
            runtime_series = -1
            throughput = np.array([-1])
            energy = np.array([-1])
            area = np.array([-1])
            power = -1
            l1_size = -1    
            l2_size = -1
            l1_size_series = -1
            l2_size_series = -1
            activity_count = -1
            mac = -1
            self.observation = [np.mean(x) for x in [runtime, throughput, energy, area, l1_size, l2_size, mac, power, num_pe]]
            print("Error in reading csv file")
        
        obs = [runtime, throughput, energy, np.array(area)]
        print("[Env Helpers][Observation: ]", obs)
        flat_obs = np.concatenate([x.flatten() for x in obs])

        # convert to numpy array
        flat_obs = np.asarray(flat_obs)
        return flat_obs
    
    def decode_action_list_multiagent (self, action_list):
        return NotImplementedError

    
    def map_to_discrete(self, action_list, discrete_values):
        discrete_action_list = []
        for i, action in enumerate(action_list):
            num_values = discrete_values[i]
            discrete_action = int(action * num_values)
            discrete_action = min(discrete_action, num_values - 1)  # Ensure the index doesn't go out of bounds
            discrete_action_list.append(discrete_action)
        return discrete_action_list

    def decode_action_list_rl (self, action_list, dimensions):

        '''
        Convert the continuous action list to a discrete action list depending upon the dimensions
        of the network layer
        '''
        print("Action List: ", action_list)
        print("Dimensions: ", dimensions)
        discrete_values = [720, 4, 2, 2, dimensions["K"], dimensions["C"], dimensions["X"],
                            dimensions["Y"], 4, 2, 2, dimensions["K"], dimensions["C"], dimensions["X"],
                              dimensions["Y"], 720, 1024]
        
        discrete_action_list = self.map_to_discrete(action_list, discrete_values)
        
        return discrete_action_list

    def generate_maestro_parameter_set(self, dimensions):
        print("Dimensions: ", dimensions)

        params = {}
        params["seed_l2"] = [i for i in range(0, 720)]
        params["ckxy_l2"] = [0, 1, 2, 3]
        params["s_l2"] = [i for i in range(dimensions["S"]-1, dimensions["S"])]
        params["r_l2"] = [i for i in range(dimensions["R"]-1, dimensions["R"])]
        params["k_l2"] = [i for i in range(1, dimensions["K"])]
        params["c_l2"] = [i for i in range(1, dimensions["C"])]
        params["x_l2"] = [i for i in range(1, dimensions["X"])]
        params["y_l2"] = [i for i in range(1, dimensions["Y"])]
        params["ckxy_l1"] = [0, 1, 2, 3]
        params["s_l1"] = [i for i in range(dimensions["S"]-1, dimensions["S"])]
        params["r_l1"] = [i for i in range(dimensions["R"]-1, dimensions["R"])]
        params["k_l1"] = [i for i in range(1, dimensions["K"])]
        params["c_l1"] = [i for i in range(1, dimensions["C"])]
        params["x_l1"] = [i for i in range(1, dimensions["X"])]
        params["y_l1"] = [i for i in range(1, dimensions["Y"])]
        params["seed_l1"] = [i for i in range(0, 720)]
        params["num_pe"] = [i for i in range(1, 1024)]

        return params

    def custom_list_representer(self, dumper, data):
        return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

    def generate_aco_maestro_config(self, yaml_file, params_dict):
        write_ok = False
        print("YAML file: ", yaml_file)
        print(os.path.exists(yaml_file))
        dumper = CustomListDumper(yaml.SafeDumper)
        yaml.add_representer(list, self.custom_list_representer, Dumper=dumper)

        try:
            with open(yaml_file, 'r') as file:
                yaml_data = yaml.safe_load(file)

            # Update the ArchParamsNode attributes with new_values
            arch_params_node = yaml_data['Nodes']['ArchParamsNode']['attributes']
            
            for key, value in params_dict.items():
                if key in arch_params_node:
                    print("Key: ", key, " Value: ", value)
                    arch_params_node[key] = value

            print("YAML data: ", yaml_data)
            
            # Save the modified YAML data back to the file
            with open(yaml_file, 'w') as file:
               yaml.dump(yaml_data, file, Dumper=CustomListDumper)

            write_ok = True
        except Exception as e:
            print(e)
            write_ok = False
        return write_ok

# For testing 
if __name__ == "__main__":   
    print("Hello!")
    
    helper = helpers()
    action_dict = {}
    action_dict["core_dispatch_width"] = 8
    action_dict["core_window_size"] = 512
    action_dict["l1_icache_size"] = 128
    action_dict["l1_dcache_size"] = 128
    action_dict["l2_cache_size"] = 2048
    action_dict["l3_cache_size"] = 8192

    helper.read_modify_write_sniper_config(action_dict)
    

    