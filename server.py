# Processing time of a packet
processing_time = 0.004

class Server:
	def __init__(self, address):
		self.id = address
		self.packet_history = []
		self.last_time=0
		self.throughput_rate=0

	def add_packet(self, packet):
		self.packet_history.append(packet)
		# packet.end_time=current_time

	def clear_packets(self):
		self.packet_history.clear()

	#calculate the load on the server
	def get_load(self, current_time):
		if len(self.packet_history) == 0:
			return 0
		TTF = 0
		t = 0
		i = 0
		count=0
		while t < current_time:
			if i >= len(self.packet_history):
				break
			packet_i = self.packet_history[i]
			if packet_i.time_sent > current_time:
				break
			if TTF > 0:
				TTF -= (packet_i.time_sent - t)
				if TTF < 0:
					count += 1
					TTF = 0
			TTF += processing_time
			t = packet_i.time_sent
			i += 1
			packet_i.end_time = packet_i.time_sent + TTF
		TTF -= (current_time - t)
		if TTF < 0:
			TTF = 0

		#calculating the throughput rate
		time_elapsed=current_time-self.last_time
		self.throughput_rate=count/time_elapsed if time_elapsed>0 else 0
		self.last_time=current_time

		return TTF

	def __repr__(self):
		string = ""
		for packet in self.packet_history:
			string += str(round(packet.time_sent,3)) + " "
		return "Server id -->" + str(self.id) +" and " + "Packet arrival times: " + string