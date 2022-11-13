# do not import anything else from loss_socket besides LossyUDP
import struct
import time
from concurrent.futures import ThreadPoolExecutor

from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY


class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.next_seq_no = 0
        self.seq_no = 0

        self.send_buffer = {}

        self.buffer = {}
        self.remove_key = []
        self.closed = False
        self.ack = 0
        self.ack_no = 0

        self.time_out = 0.25  # threshold value
        self.retransmission = False

        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(self.listener)

    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!


        while len(data_bytes) >= 1460:
            tmp_bytes = data_bytes[0:1460]
            packet = struct.pack('i i i' + str(len(tmp_bytes)) + 's', self.seq_no, self.ack, self.ack_no, tmp_bytes)
            # print("send_seq_no=", self.seq_no, "tmp_bytes", len(tmp_bytes), "tmp_bytes=", tmp_bytes)
            data_bytes = data_bytes[1460:]
            self.send_buffer[self.seq_no] = (time.time(),packet)
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            self.seq_no += 1

        # for now I'm just sending the raw application-level data in one UDP payload
        if len(data_bytes) >= 0:
            packet = struct.pack('i i i' + str(len(data_bytes)) + 's', self.seq_no, self.ack, self.ack_no, data_bytes)
            print("send_seq_no=", self.seq_no, "data_bytes", len(data_bytes), "ack=", self.ack)
            self.send_buffer[self.seq_no] = (time.time(), packet)
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            self.seq_no += 1

        #index = 0 # record which packet is going to lose

        for i in self.send_buffer.copy():
            if i <= self.ack_no:
                self.send_buffer.pop(i)
                continue
            if time.time() - self.send_buffer[i][0] > self.time_out:
                #index = i
                self.retransmission = True

        if self.retransmission:
            for p in self.send_buffer:
                self.socket.sendto(self.send_buffer[i][1], (self.dst_ip, self.dst_port))

        if len(self.send_buffer) == 0:
            self.ack = 0
            print("go here")

    def process_dict_packets(self, multiple_output):
        # print("next_seq_no=", self.next_seq_no)
        for key, val in self.buffer.copy().items():  # since multithreading, we need to make copy while we iterate through
            if key == self.next_seq_no:
                self.next_seq_no += 1
                print("seq num matches", key, "next_seq_no", self.next_seq_no)
                self.remove_key.append(key)
                multiple_output += val

        if multiple_output != b"":
            if len(self.remove_key) != 0:
                for _, val in enumerate(self.remove_key):
                    self.buffer.pop(val)
                self.remove_key.clear()
            return multiple_output
        return b""


    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        # your code goes here!  The code below should be changed!
        return self.process_dict_packets(b"")

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        self.closed = True
        self.socket.stoprecv()
        pass

    def listener(self):
        while not self.closed:  # a later hint will explain self.closed
            try:
                data, addr = self.socket.recvfrom()
                if len(data) == 0:
                    return data
                # store the data in the receive buffer
                packet = struct.unpack('i i i' + str(len(data) - 12) + 's', data)
                recv_seq_no = packet[0]
                self.ack_no = packet[2]
                recv_data = packet[3]
                self.ack = packet[1]
                print("len of data: ", len(recv_data))
                if len(recv_data) <= 1:
                    self.next_seq_no = self.ack_no+1
                    print("server side: only ack received and ack==", self.ack)
                    continue

                # print("recv_seq_no=", recv_seq_no, "recv_data=", recv_data, "ack is=", self.ack)
                #print("buffer size=", len(self.buffer), "buffer==", self.buffer)
                print("recv_seq_no=", recv_seq_no, "nextSeq_no=", self.next_seq_no)

                if recv_seq_no == self.next_seq_no:
                    # print("client ready to ack")
                    self.ack = 1
                    self.ack_no = recv_seq_no
                    self.seq_no = recv_seq_no
                    self.send(b'')

                self.buffer[recv_seq_no] = recv_data

            except Exception as e:
                print(" listener died !")
                print(e)

