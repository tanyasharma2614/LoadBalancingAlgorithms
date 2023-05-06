import random
import matplotlib.pyplot as plt
import numpy as np
from copy import deepcopy
import heapq
# Packet generation variables
num_flows = 150
mean_flow_size = 15
flow_size_stdev = 2
max_flow_duration = 0.05
# Num clients, load balancers, servers
num_clients = 50
num_load_balancers = 2
num_servers = 5
next_server = 0
weights = [random.randint(1, 10) for _ in range(num_servers)]
print(weights)
curr_weights = deepcopy(weights)
next_weight_server = 0
# Server processing time, time per packet
# processing_time = 0.004

#value for powers of x choices
powers_of_x_value = 3
heap = [(0, server) for server in range(num_servers)]
heapq.heapify(heap)

#whether or not a load balancer drops
LOAD_BALANCER_DROPS = False
assignment_methods = ["RandomAssignment", "ConsistentHashing", "PowersOfTwoNoMemory", "PowersOfTwoWithMemory", 
"PowersOfXWithMemory", "RoundRobin", "WeightedRoundRobin", "Heaps"]
assignment_methods = ["Heaps"]
powers_of_x = [2, 4, 8]

#class defining a client/host
class Client:
	def __init__(self, address):
		self.id = address

#class defining the load balancer
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

#class defining a backend server clients are making requests to 
class Server:
	def __init__(self, address):
		self.id = address
		self.packet_history = []

	def add_packet(self, packet):
		self.packet_history.append(packet)

	def clear_packets(self):
		self.packet_history.clear()

	#calculate the amount of time until the queue is theoretically free
	def get_load(self, current_time):
		if len(self.packet_history) == 0:
			return 0
		TTF = 0
		t = 0
		i = 0
		while t < current_time:
			if i >= len(self.packet_history):
				break
			packet_i = self.packet_history[i]
			if packet_i.time_sent > current_time:
				break
			if TTF > 0:
				TTF -= (packet_i.time_sent - t)
				if TTF < 0:
					#print("made zerooooooo")
					TTF = 0
			TTF += packet_i.processing_time
			t = packet_i.time_sent
			i += 1
		TTF -= (current_time - t)
		if TTF < 0:
			TTF = 0
		return TTF
		#return len(self.packet_history)*processing_time

	def __repr__(self):
		string = ""
		for packet in self.packet_history:
			string += str(round(packet.time_sent,3)) + " "
		return "Server id: " + str(self.id) +"\n" + "Packet arrival times: " + string

#class defining a packet
class Packet:
	def __init__(self, clientid, port_number,time_sent):
		self.clientid = clientid
		self.port_num = port_number
		self.time_sent = time_sent
		self.processing_time = random.uniform(0.001, 0.1)

	def __repr__(self):
		return "Packet from client: " + str(self.clientid) + "at port: " + str(self.port_num) +  " @time: " + str(round(self.time_sent,3))

def run_load_plotter(servers, assignment_method):
	# Post-Simulation Analysis
	for server in servers:
		#print(server)
		times = []
		loads = []
		for t in [x/250 for x in range(1, 250)]:
			load = server.get_load(t)
			# print("Load at time", t, "is", round(load, 3))
			times.append(t)
			loads.append(load)

		plt.plot(np.array([x for x in times]), np.array([y for y in loads]), label=str("Server" + str(server.id))) # , s=5
		plt.legend(loc="best")
		plt.xlabel('Time')
		plt.ylabel('Load (Time til finish)')
		plt.title('Load vs. Time for Servers')
		#plt.axis([0, 1, 0, 0.6])

	plt.savefig('plots/SmallSystemWithFlows/' + assignment_method + '/LoadVsTimeForServers.png')
	plt.clf()

def run_mean_and_stdev_plotter(servers, assignment_method):
	times = []
	means = []
	stdevs = []
	for t in [x/250 for x in range(1, 250)]:
		times.append(t)
		mean = sum([x.get_load(t) for x in servers]) / len(servers)
		stdev = pow( sum([((x.get_load(t) - mean) ** 2) for x in servers]) / (len(servers) - 1), 1/2)
		means.append(mean)
		stdevs.append(stdev)
		
	plt.plot(np.array([x for x in times]), np.array([y for y in means]), label="mean")
	plt.plot(np.array([x for x in times]), np.array([y for y in stdevs]), label="stdev")

	avg_mean = sum(means)/len(means)
	avg_stdev = sum(stdevs)/len(stdevs)

	print("Mean load: %5.3f" % avg_mean)
	print("Mean standard deviation: %5.3f" % avg_stdev)

	plt.legend(loc="best")
	plt.xlabel('Time')
	plt.ylabel('Mean / stdev server load')
	plt.title('Mean and Stdev of Load vs. Time for Servers')
	plt.axis([0, 1, 0, 0.6])

	plt.savefig('plots/SmallSystemWithFlows/' + assignment_method + '/MeanAndStdevLoadVsTimeForServers.png')
	plt.clf()

def run_consistency_check(servers):
	perFlowConsistent = True
	for server in servers:
		for otherServer in servers:
			if server.id != otherServer.id:
				for packet in server.packet_history:
					if (packet.clientid, packet.port_num) in [(pckt.clientid, pckt.port_num) for pckt in otherServer.packet_history]:
						#print(packet.clientid, " and ", packet.port_num)
						perFlowConsistent = False
						break

	if perFlowConsistent:
		print("Per-Flow Consistency Maintained")
	else:
		print("Per-Flow Consistency Not Maintained")


server_list = []
def run_simulation(assignment_method):
	print("running simulation for " + assignment_method)

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
	run_consistency_check(servers)
	print()

for method in assignment_methods:
	run_simulation(method)