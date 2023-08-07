from TCP_socket_p2 import TCP_Connection

class TCP_Connection_Final(TCP_Connection):
    def __init__(self, self_address, dst_address, self_seq_num, dst_seq_num, log_file=None):
        super().__init__(self_address, dst_address, self_seq_num, dst_seq_num, log_file)

    def handle_timeout(self):
        if self.send_buff:
            # Resend the oldest unacknowledged packet
            packet = self.send_buff[0]
            psh_flag = (packet['flags'] & 0x08) != 0
            self._packetize_and_send(packet['SEQ'], PSH=psh_flag, data=packet['data'])
            # Increase the RTO timer
            self.RTO_timer.set_length(self.RTO_timer.timer_length * 2)

    def handle_window_timeout(self):
        if not self.send_buff:
            # Send a packet containing the most recent data
            if self.last_packet[0] != -1:
                self._packetize_and_send(self.last_packet[0], PSH=self.last_packet[1], data=self.last_packet[2])
            # Increase the window timer
            self.window_timer.set_length(self.window_timer.timer_length * 2)

    def receive_packets(self, packets):
        for packet in packets:
            # Read packet data into the receive buffer
            seq_num = packet['SEQ']
            data = packet['data']
            if seq_num >= self.receive_buffer_start_seq and seq_num < self.receive_buffer_start_seq + self.RCV.WND:
                index = seq_num - self.receive_buffer_start_seq
                self.receive_buffer[index] = data[:self.RCV.MSS]
                psh_flag = (packet['flags'] & 0x08) != 0
                if psh_flag:
                    self.receive_buffer[index] += b'PSH'
            # Update RTT timer and RTO timer
            if seq_num == self.RTT_Sequence_num:
                self.RTT_timer.stop_timer()
                self.RTT_timer.reset_timer()
                self.RTT_timer.set_and_start(self.RTT_timer.timer_length)
                self.RTO_timer.set_length(self.RTT_timer.check_time() * 2)

    def send_data(self, window_timeout=False, RTO_timeout=False):
        if not window_timeout and not RTO_timeout:
            # Load the correct data from the send buffer and send a single packet
            if self.send_buff:
                packet = self.send_buff[0]
                psh_flag = (packet['flags'] & 0x08) != 0
                self._packetize_and_send(packet['SEQ'], PSH=psh_flag, data=packet['data'])
                # Update congestion control window
                self.congestion_window = min(self.congestion_window, self.SND.WND)
                # Set the RTT timer
                if not self.RTT_timer.is_running():
                    self.RTT_timer.set_and_start(self.RTT_timer.timer_length)
        elif RTO_timeout:
            # Resend the oldest unacknowledged packet
            self.handle_timeout()
        elif window_timeout:
            # Send a packet containing the most recent data
            if self.last_packet[0] != -1:
                self._packetize_and_send(self.last_packet[0], PSH=self.last_packet[1], data=self.last_packet[2])