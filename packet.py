class Packet:
    def __init__(self, clientid, port_number,time_sent):
        self.clientid = clientid
        self.port_num = port_number
        self.time_sent = time_sent
        self.end_time = time_sent
        self.processing_time = 0.004
        #self.processing_time = random.uniform(0.001, 0.1)
        
    def __repr__(self):
        return "Packet from the client--->" + str(self.clientid) + "from port--->" + str(self.port_num) +  " at time: " + str(round(self.time_sent,3))