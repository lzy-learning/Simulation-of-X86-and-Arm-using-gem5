import os
import sys
import m5
from m5.objects import *
from gem5.isas import ISA
from gem5.runtime import get_runtime_isa

from argparse import ArgumentParser


parser = ArgumentParser(description='Simlution X86 and ARM architecture writed by linzhy.')

parser.add_argument('--cpu-type', 
                    default='X86MinorCPU',
                    help='Type of CPU model.')

parser.add_argument('--caches',
                    action='store_true',
                    default=False,
                    help='Add this option to use cache.')

parser.add_argument('--l2cache',
                    action='store_true',
                    default=False,
                    help='Add this option to use L2 cache.')

parser.add_argument('--l1i_size',
                    default='32kB',
                    help='The size of instruction L1 cache.')

parser.add_argument('--l1d_size',
                    default='32kB',
                    help='The size of data L1 cache.')

parser.add_argument('--l2_size',
                    default='512kB',
                    help='The size of L2 cache.')

parser.add_argument('--l1i_assoc',
                    default=2,
                    help='Associativity of L1 instruction cache.')

parser.add_argument('--l1d_assoc',
                    default=2,
                    help='Associativity of L1 data cache.')

parser.add_argument('--l2_assoc',
                    default=8,
                    help='Associativity of L2 cache.')

parser.add_argument('--mem-type',
                    default='DDR3_1600_8x8',
                    help='Type of memory.')

parser.add_argument('--cmd',
                    default='',
                    required=True,
                    help='The binary to run in syscall emulation mode.')

parser.add_argument('--options',
                    default='',
                    help='The options to pass to the binary, use around the entire string')

parser.add_argument('--output',
                    default='',
                    help='Redirect stdout to a file.')

args = parser.parse_args()

# Base classes for data L1cache and instruction L1cache
class L1Cache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def __init__(self, options=None):
        super(L1Cache, self).__init__()
        pass

    def connectBus(self, bus):
        """Connect this cache to a memory-side bus"""
        self.mem_side = bus.cpu_side_ports

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU-side port
        This must be defined in a subclass"""
        raise NotImplementedError
    

class L1ICache(L1Cache):
    '''L1 instruction cache'''
    # Set the default size
    size = "32kB"

    def __init__(self, opts=None):
        super(L1ICache, self).__init__(opts)
        if not opts or not opts.l1i_size:
            return
        self.size = opts.l1i_size

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU icache port"""
        self.cpu_side = cpu.icache_port


class L1DCache(L1Cache):
    '''L1 data cache'''
    # Set the default size
    size = "32kB"

    def __init__(self, opts=None):
        super(L1DCache, self).__init__(opts)
        if not opts or not opts.l1d_size:
            return
        self.size = opts.l1d_size

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU dcache port"""
        self.cpu_side = cpu.dcache_port


class L2Cache(Cache):
    '''L2 cache'''
    # Default parameters
    size = "512kB"
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12

    def __init__(self, opts=None):
        super(L2Cache, self).__init__()
        if not opts or not opts.l2_size:
            return
        self.size = opts.l2_size

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports

thispath = os.path.dirname(os.path.realpath(__file__))
default_binary = '/home/linzhy/automotive/basicmath/basicmath_small'

system = System()

system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"  # Use timing accesses
system.mem_ranges = [AddrRange("512MB")]  # Create an address range

system.cpu = eval(args.cpu_type)()


system.cpu.icache = L1ICache(args)
system.cpu.dcache = L1DCache(args)

system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

system.l2bus = L2XBar()

system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)

system.l2cache = L2Cache(args)
system.l2cache.connectCPUSideBus(system.l2bus)

system.membus = SystemXBar()

system.l2cache.connectMemSideBus(system.membus)

system.cpu.createInterruptController()
# if m5.defines.buildEnv['TARGET_ISA'] == "x86":
if get_runtime_isa() != ISA.ARM:
    system.cpu.interrupts[0].pio = system.membus.mem_side_ports
    system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

# Create a DDR3 memory controller
system.mem_ctrl = MemCtrl()
# system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram = eval(args.mem_type)()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# system.workload = SEWorkload.init_compatible(args.cmd)
# process = Process()
# process.cmd = [args.cmd]
# system.cpu.workload = process
# system.cpu.createThreads()

process = Process()
process.executable = args.cmd
process.cwd = os.getcwd()
process.gid = os.getgid()
if args.options != "":
    process.cmd = [args.cmd] + args.options.split()
else:
    process.cmd = args.cmd
if args.output != '':
    process.output = args.output

system.cpu.workload = process
system.cpu.createThreads()
system.workload = SEWorkload.init_compatible(process.executable)

root = Root(full_system=False, system=system)

m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause()))