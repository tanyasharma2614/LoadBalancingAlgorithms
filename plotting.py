import matplotlib.pyplot as plt
import numpy as np

def run_load_plotter(servers, lb_strategy, system_type):
	for server in servers:
		times = []
		loads = []
		for t in [x/250 for x in range(1, 250)]:
			load = server.get_load(t)
			times.append(t)
			loads.append(load)

		plt.plot(np.array([x for x in times]), np.array([y for y in loads]), label=str("Server" + str(server.id)))
		plt.legend(loc="best")
		plt.xlabel('Time')
		plt.ylabel('Load (Time to finish)')
		plt.title('Load vs. Time for Servers')

	plt.savefig('plots/{}/{}/LoadVsTimeForServers.png'.format(system_type, lb_strategy))
	plt.clf()

def run_response_time_plotter(servers, lb_strategy, system_type):
    for server in servers:
        times = []
        response_times = []
        for t in [x / 250 for x in range(1, 250)]:
            times.append(t)
            response_times_t = []
            for packet in server.packet_history:
                if packet.end_time <= t:
                    response_times_t.append(packet.end_time - packet.start_time)
            if len(response_times_t) > 0:
                response_times.append(sum(response_times_t) / len(response_times_t))
            else:
                response_times.append(0)
        plt.plot(times, response_times, label=f"Server {server.id}")
    plt.legend(loc="best")
    plt.xlabel('Time')
    plt.ylabel('Response Time')
    plt.title('Response Time vs. Time for Servers')
    plt.savefig('plots/{}/{}/ResponseTimeVsTimeForServers.png'.format(system_type, lb_strategy))
    plt.clf()

def run_mean_and_stdev_plotter(servers, lb_strategy, system_type):
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

	plt.savefig('plots/{}/{}/MeanAndStdevLoadVsTimeForServers.png'.format(system_type, lb_strategy))
	plt.clf()
	
def run_throughput_plotter(servers, lb_strategy, system_type):
    for server in servers:
        times = []
        throughputs = []  # initialize list to store throughput values
        for t in [x / 250 for x in range(1, 250)]:
            load = server.get_load(t)
            throughput = server.throughput_rate  # get the throughput rate from the server object
            times.append(t)
            throughputs.append(throughput)  # add the throughput rate to the lis
	
        plt.plot(np.array([x for x in times]), np.array([y for y in throughputs]), label=str("Server" + str(server.id)) + ' Throughput')
        plt.legend(loc="best")
        plt.xlabel('Time')
        plt.ylabel(' Throughput')
        plt.title('Throughput vs. Time for Servers')

    plt.savefig('plots/{}/{}/ThroughputVsTimeForServers.png'.format(system_type, lb_strategy))
    plt.clf()

def run_consistency_check(servers):
	perFlowConsistent = True
	for server in servers:
		for otherServer in servers:
			if server.id != otherServer.id:
				for packet in server.packet_history:
					if (packet.client_id, packet.port_number) in [(pckt.client_id, pckt.port_number) for pckt in otherServer.packet_history]:
						perFlowConsistent = False
						break

	if perFlowConsistent:
		print("Per-Flow Consistency Maintained")
	else:
		print("Per-Flow Consistency Not Maintained")