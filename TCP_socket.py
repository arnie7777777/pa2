from TCP_socket_p2 import TCP_Connection
import time

class TCP_Connection_Final(TCP_Connection):
    def __init__(self, self_address, dst_address, self_seq_num, dst_seq_num, log_file=None):
        super().__init__(self_address, dst_address, self_seq_num, dst_seq_num, log_file)

    def handle_timeout(self):
        if self.last_packet[0] != -1:
            self._packetize_and_send(self.last_packet[0], PSH=self.last_packet[1], data=self.last_packet[2])
            self.RTO_timer.set_and_start(2 * self.RTO_timer.timer_length)
            self.SSTHRESH = max(self.SND.WND // 2, 2 * self.SND.MSS)
            self.congestion_window = self.SND.MSS

    def handle_window_timeout(self):
        self._packetize_and_send(self.SND.NXT)

    def receive_packets(self, packets):
        # SEND_BUFF_SIZE = 8192
        # RECV_BUFF_SIZE = 8192
        # ALPHA = 1/8
        # BETA = 1/4
        for packet in packets:
            if packet.SEQ < self.RCV.NXT:
                continue
            if packet.SEQ == self.RCV.NXT:
                while self.receive_buffer_start_seq + self.RCV.WND < packet.SEQ + packet.LEN:
                    self.receive_buffer.append(packet.data[:self.receive_buffer_start_seq + self.RCV.WND - packet.SEQ])
                    packet.data = packet.data[self.receive_buffer_start_seq + self.RCV.WND - packet.SEQ:]
                    self.RCV.WND += len(self.receive_buffer[-1])
                    self.receive_buffer_start_seq += len(self.receive_buffer[-1])
                self.receive_buffer.append(packet.data)
                self.RCV.WND += len(packet.data)
                self.receive_buffer_start_seq += len(packet.data)
                while self.receive_buffer[0] is not None:
                    self.receive_buffer.popleft()
                    self.RCV.WND -= 1
                    self.receive_buffer_start_seq += 1
            elif self.receive_buffer_start_seq <= packet.SEQ < self.receive_buffer_start_seq + self.RCV.WND:
                self.receive_buffer[packet.SEQ - self.receive_buffer_start_seq] = packet.data
            if packet.flags.ACK:
                self.RTO_timer.stop_timer()
                self.RTT_timer.stop_timer()
                if self.RTT_Sequence_num != -1:
                    sample_RTT = time.time() - self.RTT_timer.start_time
                    if self.SRTT is None:
                        self.SRTT = sample_RTT
                        self.RTTVAR = sample_RTT / 2
                    else:
                        self.RTTVAR = (1 - BETA) * self.RTTVAR + BETA * abs(self.SRTT - sample_RTT)
                        self.SRTT = (1 - ALPHA) * self.SRTT + ALPHA * sample_RTT
                    self.RTO_timer.set_and_start(self.SRTT + max(1, 4 * self.RTTVAR) if self.RTTVAR is not None else 0)
                    self.SND.WND = min(self.SSTHRESH, packet.WND) + packet.ACK - self.SND.UNA
                    self.RTT_Sequence_num = -1
            if packet.flags.SYN:
                self.SND.NXT = packet.SEQ + 1
                self.RCV.IRS = packet.SEQ
                self.SND.UNA = packet.ACK
                self.SND.WND = packet.WND
            if packet.flags.FIN:
                self.RCV.NXT += 1

    def send_data(self, window_timeout=False, RTO_timeout=False):
        if not window_timeout and not RTO_timeout:
            self.last_packet = [self.SND.NXT, False, b'']
            self.window_timer.set_and_start(0.5)
            self.RTO_timer.set_and_start(self.SRTT + max(1, 4 * self.RTTVAR) if self.RTTVAR is not None else 0)
            self.RTT_Sequence_num = self.SND.NXT
            if self.SSTHRESH is None:
                self.SSTHRESH = self.SND.WND
        
        while self.send_buff and self.SND.NXT < self.SND.UNA + self.SND.WND:
            data = self.send_buff.pop(0)
            if isinstance(data, int):  # Check if data is an integer
                data = bytes([data % 256])  # Convert integer to bytes
            remaining_space = min(self.SND.UNA + self.SND.WND - self.SND.NXT, self.SND.MSS)
            
            while len(data) > 0:
                self._packetize_and_send(self.SND.NXT, PSH=True, data=data[:remaining_space])
                data = data[remaining_space:]
                self.SND.NXT += remaining_space
                remaining_space = min(self.SND.UNA + self.SND.WND - self.SND.NXT, self.SND.MSS)
                self.RTT_timer.reset_timer()
            
            self._packetize_and_send(self.SND.NXT, PSH=False, data=data)
            self.SND.NXT += len(data)
            
            if not window_timeout and not RTO_timeout:
                self.last_packet = [self.SND.NXT, False, data]
        
        self.window_timer.reset_timer()
