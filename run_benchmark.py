import os
import re

cur_root = os.path.dirname(os.path.abspath(__file__))

builder_list = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'build/ARM/gem5.opt'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'build/X86/gem5.opt')
    # '/home/linzhy/Documents/gem5-stable/build/ARM/gem5.opt',
    # '/home/linzhy/Documents/gem5-stable/build/X86/gem5.opt'
]


system_emulation_path = os.path.join(cur_root, 'simulate.py')

# corresponding commands for testing programs
benchmark_cmd_list = [
    'basicmath/basicmath_small > output_small.txt',
    'dijkstra/dijkstra_small dijkstra/input.dat > output_small.dat',  # large: dijkstra_large
    'qsort/qsort_small qsort/input_small.dat > output_small.txt',    # large: input_large.dat
    'bitcount/bitcnts 75000 > output_small.txt',         # large: 1125000
    'patricia/patricia patricia/small.udp > output_small.txt'     # large: large.udp
]

# cpu & caches configuration
cpu_type_list = []
cache_size_list = [('32kB','512kB'),  ('64kB','1MB')]

# output directory to store the output of benchmark programs
output_root_path = os.path.join(cur_root, 'benchmark_output')

# number of repetitions per simulation
num_repeat_per_sim = 4

# the location where indicator datas are saved after each simulation
stats_path = os.path.join(cur_root, 'm5out/stats.txt')

# where experiment result stored
result_path = os.path.join(cur_root, 'sim_result.txt')


def extract_stats_for_evaluate(file_path):
    '''
    extract stats from 'stats.txt'
    '''
    stats = {}

    with open(file_path, 'r') as file:
        content = file.read()

        # Extract CPI
        cpi_match = re.search(r'system\.cpu\.cpi\s+(\d+\.\d+)', content)
        if cpi_match:
            stats['CPI'] = float(cpi_match.group(1))
        else:
            print("something wrong when extract cpi")

        # Extract L2 cache miss rate
        l2_miss_rate_match = re.search(r'system.l2cache.overallMissRate::total\s+(\d+\.\d+)', content)
        if l2_miss_rate_match:
            stats['L2 Cache Miss Rate'] = float(l2_miss_rate_match.group(1))
        else:
            print("something wrong when extract l2 cache miss rate")

        # Extract Total Energy (mJ)
        voltage_match = re.search(r'system.clk_domain.voltage_domain.voltage\s+(\d+)', content)
        ipc_match = re.search(r'system.cpu.ipc\s+(\d+\.\d+)', content)
        l1dcache_miss_match = re.search(r'system.cpu.dcache.overallMisses::total\s+(\d+)', content)
        l1icache_miss_match = re.search(r'system.cpu.icache.overallMisses::total\s+(\d+)', content)
        l2cache_miss_match = re.search(r'system.l2cache.overallMisses::total\s+(\d+)', content)
        sim_time_match = re.search(r'simSeconds\s+(\d+\.\d+)', content)

        if voltage_match and ipc_match and l1dcache_miss_match and l1icache_miss_match and l2cache_miss_match:
            sim_time = float(sim_time_match.group(1))
            voltage = float(voltage_match.group(1))
            ipc = float(ipc_match.group(1))
            cache_miss_count = float(l1dcache_miss_match.group(1))+float(l1icache_miss_match.group(1))+float(l2cache_miss_match.group(1))
            stats['Total Energy (mJ)'] = voltage*(2*ipc+3 * 0.000000001 * cache_miss_count)* sim_time * 1000
            # print('cpu energy: ', stats['Total Energy (mJ)'])
        else:
            print('something wrong where calculate CPU energy consum.')

        energy_match = re.findall(r'system.mem_ctrl.dram.rank\d.totalEnergy\s+(\d+)', content)
        if energy_match:
            if 'Total Energy (mJ)' not in stats.keys():
                stats['Total Energy (mJ)'] = 0.0
            for match in energy_match:
                stats['Total Energy (mJ)'] += float(match) / 1e9
        else:
            print("something wrong when extract mem energy")

        # Extract Throughput (KB/s)
        throughput_match = re.search(r'system.mem_ctrl.dram.bwTotal::total\s+(\d+)', content)
        if throughput_match:
            stats['Throughput (KB/s)'] = float(throughput_match.group(1)) / 1024.0
        else:
            print("something wrong when extract throughput")

    return stats


def run():
    '''
    run simulation serially
    '''
    for benchmark_cmd in benchmark_cmd_list:
        params = benchmark_cmd.split(' ')
        # diff isa
        for builder in builder_list:
            cmd = builder
            cmd = cmd + ' ' + system_emulation_path
            
            # add some fixed parameters
            cmd = cmd + ' ' + '--caches'
            cmd = cmd + ' ' + '--l2cache'
            cmd = cmd + ' ' + '--l1i_assoc=2'
            cmd = cmd + ' ' + '--l1d_assoc=2'
            cmd = cmd + ' ' + '--l2_assoc=8'
            cmd = cmd + ' ' + '--mem-type=DDR3_1600_8x8'

            if 'X86' in builder:
                benchmark_path = os.path.join(cur_root, 'bench_x86')
                cpu_type_list = ['X86MinorCPU', 'X86O3CPU']
            else:
                benchmark_path = os.path.join(cur_root, 'bench_arm')
                cpu_type_list = ['ArmMinorCPU', 'ArmO3CPU']
            
            cmd = cmd +' ' +f'--cmd={os.path.join(benchmark_path, params[0])}'
            
            cmd_tmp1 = cmd

            # diff cpu type
            for cpu_type in cpu_type_list:
                cmd = cmd + ' ' + f'--cpu-type={cpu_type}'

                cmd_tmp2 = cmd

                # diff cahce size
                for (l1_cache_size, l2_cache_size) in cache_size_list:
                    cmd = cmd+' '+f'--l1i_size={l1_cache_size}'
                    cmd = cmd+' '+f'--l1d_size={l1_cache_size}'
                    cmd = cmd+' '+f'--l2_size={l2_cache_size}'
                    if len(params) > 3:
                        # the input is specified by a file
                        if '/' in params[1]:
                            cmd = cmd +' '+'--options='+os.path.join(benchmark_path, params[1])
                        # the input is number
                        else:
                            cmd = cmd +' '+'--options='+params[1]
                    
                    avg_cpi = 0.0
                    avg_l2CahceMissRate = 0.0
                    avg_totalEnergy = 0.0
                    avg_throughput = 0.0
                    num_valid = 0

                    cmd_tmp3 = cmd

                    for t in range(num_repeat_per_sim):
                        output_path = params[0].split('/')[-1]+'_' \
                        +builder.split('/')[-2]+'_' \
                        +cpu_type+'_' \
                        +f'l1_{l1_cache_size}'+'_' \
                        +f'l2_{l2_cache_size}'+ f'_{t}' + '.txt'
                        # specified the output path
                        cmd = cmd +' '+f'--output={os.path.join(output_root_path, output_path)}'

                        os.system(cmd)

                        # extract the metrics
                        stats = extract_stats_for_evaluate(stats_path)
                        cpi = stats.get('CPI', -1)
                        l2CacheMissRate = stats.get('L2 Cache Miss Rate', -1)
                        totalEnergy = stats.get('Total Energy (mJ)', -1)
                        throughput = stats.get('Throughput (KB/s)', -1)

                        if cpi == -1 or l2CacheMissRate == -1 or totalEnergy == -1 or throughput == -1:
                            print(output_path.split('.')[-2], ' invalid experimental: ',t)
                        else:
                            num_valid += 1
                            avg_cpi += cpi
                            avg_l2CahceMissRate += l2CacheMissRate
                            avg_totalEnergy += totalEnergy
                            avg_throughput += throughput
                        
                        cmd = cmd_tmp3
                    
                    print("==========================================")
                    print(output_path.split('.')[-1], '\t\t\t\tsimulate end!')
                    avg_cpi /= num_valid
                    avg_l2CahceMissRate /= num_valid
                    avg_totalEnergy /= num_valid
                    avg_throughput /= num_valid
                    print("Average CPI:", avg_cpi)
                    print("Average L2 Cache Miss Rate:", avg_l2CahceMissRate)
                    print("Average Total Energy:", avg_totalEnergy)
                    print("Average Throughput (KB/s):", avg_throughput)
                    print("storing......")
                    with open(result_path, 'a+') as fp:
                        fp.write(f"benchmark={params[0].split('/')[-1].split('_')[0]}\n")
                        fp.write(f"isa={'arm' if 'ARM' in builder else 'x86'}\n")
                        fp.write(f"cpu-type={'inorder'if 'Minor' in cpu_type else 'outoforder'}, L1={l1_cache_size}, L2={l2_cache_size}\n")
                        fp.write(f"CPI={avg_cpi}\n")
                        fp.write(f"L2CacheMissRate={avg_l2CahceMissRate}\n")
                        fp.write(f"TotalEnergy={avg_totalEnergy}\n")
                        fp.write(f"Throughput={avg_throughput}\n\n")
                    print("==========================================")

                    cmd = cmd_tmp2
            
            cmd = cmd_tmp1
            

if __name__ == '__main__':
    run()
