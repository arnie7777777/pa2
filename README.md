The goal of the project is to implement a simplified version of TCP (Transmission Control Protocol). The project is worth 13 points and requires information from three RFCs: RFC 5681, RFC 9293, and RFC 6298. The project has been designed to minimize the amount of work required in several ways.

The following features of TCP will not be implemented:
1. Connections: Sequence numbers must be passed out of band.
2. SWS (Silly Window Syndrome) avoidance algorithms.
3. Duplicate acknowledgments and other optional features.
The functions that need to be implemented are as follows:
1. Send packets: Load the correct data from the send buffer and send the largest packet allowed by three factors: the maximum segment size (SND.MSS), the flow control window (SND.WND), and the congestion control window (self.congestion_window).
2. Receive packets: Read packet data into the receive buffer, ensuring that data is placed in the correct position indicated by its sequence number. Trim packets so that only bytes within the receive window are read into the receive buffer.
3. Congestion control: a. RTT (Round Trip Time) timer: Start the timer when new data is sent and update the most recent RTT measurement when data is acknowledged. b. RTO (Retransmission Time Out) timer: Set the timer correctly and update it as per RFC 6298.
4. Resend packets: Whenever the RTO timer goes off, resend the oldest unacknowledged packet.
5. Flow control: Ensure that no more data is sent than the flow control window allows. Update SND.WND when a new window measurement is received.
6. Push flag: a. Send: Set the push flag whenever at least one of the bytes being sent is marked as PSH. b. Receive: Mark a byte with PSH in the receive buffer when the packet has the PSH flag set.
7. Send correct acknowledgments: Send an acknowledgement (empty packet) with the acknowledgment number (ack#) set to the next expected byte (RCV.NXT). Only send one acknowledgment per list of packets. Update RCV.NXT when appropriate.
8. Zero window probing: When a window timer goes off, send a packet containing the most recent data sent. Increase the timer by a factor of 2 when it goes off. Restart the timer whenever data is sent, including retransmissions.
The functions are divided as follows:

* handle_timeout(self): Implements functions 2b, 3, and 7.
* handle_window_timeout(self): Implements function 7.
* receive_packets(self, packets): Implements functions 1, 2a, 2b, 4, 5b, and 6.
* send_data(self, window_timeout = False, RTO_timeout = False): Implements functions 0, 2, 2a, 2b, 4, 5a, and 7.
The timeout functions are expected to be around 2-10 lines, the send function around 20-30 lines, and the receive packets function around 60 lines. The logic for all functions except receive_packets should be relatively simple.# pa2
