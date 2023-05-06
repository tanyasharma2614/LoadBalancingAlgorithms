from simulation import run_simulation

load_balance_methods = ["RandomAssignment", "ConsistentHashing", "PowersOfTwoNoMemory", "PowersOfTwoWithMemory", 
"PowersOfXWithMemory", "RoundRobin", "WeightedRoundRobin", "Heaps"]

for method in load_balance_methods:
	run_simulation(method)