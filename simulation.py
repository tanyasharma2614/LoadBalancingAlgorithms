import random
from copy import deepcopy
import heapq
import numpy as np

from packet import Packet
from server import Server
from plotting import * 
num_flows = 150
mean_flow_size = 15
flow_size_stdev = 2
max_flow_duration = 0.05
num_clients = 50
num_load_balancers = 4
num_servers = 5
LOAD_BALANCER_DROPS = False
heap = [(0, server) for server in range(num_servers)]
powers_of_x = [2, 4, 8]
powers_of_x_value = 3
heapq.heapify(heap)
next_server = 0
weights = [random.randint(1, 10) for _ in range(num_servers)]
print(weights, "are the server weights")
curr_weights = deepcopy(weights)
next_weight_server = 0

class LoadBalancer:
	def __init__(self, address):
		self.id = address
		self.connection_table = {}

	def assign_server_random(self, packet, _1, _2):
		return random.randint(0, num_servers - 1)

	def assign_server_hashing(self, packet, _1, _2):
		return hash((packet.clientid, packet.port_num)) % num_servers
	
	def assign_server_roundrobin(self, packet, _1, _2):
		global next_server
		server_num = next_server
		next_server = (next_server + 1) % num_servers
		return server_num
	
	def assign_server_weighted_roundrobin(self, packet, _1, _2):
		global curr_weights
		for i in range(len(curr_weights)):
			if curr_weights[i] > 0:
				curr_weights[i]-=1
				return i
		curr_weights = deepcopy(weights)
		return self.assign_server_weighted_roundrobin(packet, _1, _2)

	def assign_server_power_of_2_choices_no_memory(self, packet, servers, _):

		#pick 2 servers randomly
		first_query_server = random.randint(0, num_servers - 1)
		second_query_server = random.randint(0, num_servers - 1)

		#ensure 2nd server is different from 1st
		while (first_query_server == second_query_server):
			second_query_server = random.randint(0, num_servers - 1)

		#get loads of both servers
		first_query_load = servers[first_query_server].get_load(packet.time_sent)
		second_query_load = servers[second_query_server].get_load(packet.time_sent)

		#pick server with least load 
		if first_query_load < second_query_load:
			return first_query_server
		return second_query_server

	def assign_server_power_of_2_choices_with_memory(self, packet, servers, _):
		#check this is a new flow by checking header tuple
		header_tuple = (packet.clientid, packet.port_num)
		if header_tuple in self.connection_table:
			return self.connection_table[header_tuple]

		#pick 2 servers randomly
		first_query_server = random.randint(0, num_servers - 1)
		second_query_server = random.randint(0, num_servers - 1)

		#ensure 2nd server is different from 1st
		while (first_query_server == second_query_server):
			second_query_server = random.randint(0, len(servers) - 1)

		#get loads of both servers
		first_query_load = servers[first_query_server].get_load(packet.time_sent)
		second_query_load = servers[second_query_server].get_load(packet.time_sent)

		#pick server with least load, and store it in the connection table to ensure future consistency
		if first_query_load < second_query_load:
			self.connection_table[header_tuple] = first_query_server
			return first_query_server
		self.connection_table[header_tuple] = second_query_server
		return second_query_server

	def assign_server_power_of_x_choices_with_memory(self, packet, servers, x):
		#check this is a new flow by checking header tuple
		header_tuple = (packet.clientid, packet.port_num)
		if header_tuple in self.connection_table:
			return self.connection_table[header_tuple]

		if x > num_servers:
			print("Number of servers too low for power of " + str(x) + " choices.")
			return

		#pick x servers randomly
		server_nums = random.sample(range(0, num_servers), x)
		loads = []
		for num in server_nums:
			loads.append(servers[num].get_load(packet.time_sent))

		min_load_server_id = loads.index(min(loads))
		min_server_num = server_nums[min_load_server_id]

		self.connection_table[header_tuple] = min_server_num
		return min_server_num

	def __repr__(self):
		return "Load Balancer id: " + str(self.id)

def run_simulation(assignment_method):
	print("running simulation for ", assignment_method)

	# Initialization Steps
	packets = []
	for i in range(num_flows):
		num_packets_in_flow = int(np.random.normal(mean_flow_size, flow_size_stdev))
		client_of_flow = random.randint(0, num_clients-1)
		time_of_flow = random.random()
		port_number = random.randint(1024, 65536)
		for j in range(num_packets_in_flow):
			time_of_packet = time_of_flow + (random.random() * (max_flow_duration) - max_flow_duration / 2)
			packet = Packet(client_of_flow, port_number, time_of_packet)
			packets.append(packet)
	#print("len is ", len(packets))
	#packets = list(set(packets))
	packets.sort(key=lambda x: x.time_sent, reverse=False)
	#print("len is ", len(packets))
	load_balancers = []
	for i in range(num_load_balancers):
		load_balancer = LoadBalancer(i)
		load_balancers.append(load_balancer)

	servers = []
	for i in range(num_servers):
		server = Server(i)
		servers.append(server)

	#current_time = 0
	# Main Simulation Processing Loop
	for i in range(len(packets)):
		packet = packets[i]

		if LOAD_BALANCER_DROPS:
			if i < len(packets)/2:
				lb_id = packet.clientid % num_load_balancers
			else: #last load balancer "goes down"
				lb_id = packet.clientid % (num_load_balancers - 1)
		else:
			lb_id = packet.clientid % num_load_balancers

		load_balancer = load_balancers[lb_id]
		if assignment_method == "Heaps":
			current_workload, current_worker = heapq.heappop(heap)
			new_workload = current_workload + packet.processing_time
			heapq.heappush(heap, (new_workload, current_worker))
			server = servers[current_worker]
			server.add_packet(packet)
		else:
			switcher = {
				"RandomAssignment": load_balancer.assign_server_random,  # No per-flow consistency :(
				"ConsistentHashing": load_balancer.assign_server_hashing, # Per-flow consistency :)
				"PowersOfTwoNoMemory": load_balancer.assign_server_power_of_2_choices_no_memory, # No Per-flow consistency :( + Congestion control :)
				"PowersOfTwoWithMemory": load_balancer.assign_server_power_of_2_choices_with_memory, # Per-flow consistency :) + Congestion control :) 
				"PowersOfXWithMemory": load_balancer.assign_server_power_of_x_choices_with_memory, # Per-flow consistency :) + Congestion control :) 
				"RoundRobin": load_balancer.assign_server_roundrobin,
				"WeightedRoundRobin": load_balancer.assign_server_weighted_roundrobin,
			}
			func = switcher.get(assignment_method, lambda: "Invalid assignment method")
			server_id = func(packet, servers, powers_of_x_value)

			server = servers[server_id]
			server.add_packet(packet)
		

	run_load_plotter(servers, assignment_method)
	run_mean_and_stdev_plotter(servers, assignment_method)
	run_throughput_plotter(servers, assignment_method)
	run_response_time_plotter(servers,assignment_method)

	
	run_consistency_check(servers)
	print("**********************************************************************")