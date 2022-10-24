# do not import anything else from loss_socket besides LossyUDP
import struct
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY

max_packet_len = 1454


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
        self.buffer = {}
        self.remove_key = []
        self.closed = False
        self.ack = 0
        self.ack_no = 0
        self.fin = 0
        self.checksum = ""

        self.time_out = 0.1  # threshold value
        self.retransmission = False

        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(self.listener)

    def format_checksum(self, data):
        s = 0
        n = len(data) % 2
        for i in range(0, len(data) - n, 2):
            s += ord(data[i]) + (ord(data[i + 1]) << 8)
        if n:
            s += ord(data[i + 1])
        while (s >> 16):
            s = (s & 0xFFFF) + (s >> 16)
        s = ~s & 0xffff
        return s

    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!
        send_time = time.time()
        while len(data_bytes) >= max_packet_len:
            tmp_bytes = data_bytes[0:max_packet_len]
            header = struct.pack(('i i i i' + str(len(tmp_bytes)) + 's'),
                                 self.seq_no, self.ack, self.ack_no, self.fin, tmp_bytes)
            self.checksum = self.format_checksum(hashlib.sha224(header).hexdigest())
            packet = struct.pack('i i i i H' + str(len(tmp_bytes)) + 's',
                                 self.seq_no, self.ack, self.ack_no, self.fin, self.checksum, tmp_bytes)
            # print("send_seq_no=", self.seq_no, "tmp_bytes", len(tmp_bytes), "tmp_bytes=", tmp_bytes)
            data_bytes = data_bytes[max_packet_len:]
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            self.seq_no += 1

        # for now I'm just sending the raw application-level data in one UDP payload
        if len(data_bytes) >= 0:
            header = struct.pack(('i i i i' + str(len(data_bytes)) + 's'),
                                 self.seq_no, self.ack, self.ack_no, self.fin, data_bytes)
            self.checksum = self.format_checksum(hashlib.sha224(header).hexdigest())
            print("check_sum", self.checksum)
            packet = struct.pack(('i i i i H' + str(len(data_bytes)) + 's'),
                                 self.seq_no, self.ack, self.ack_no, self.fin, self.checksum, data_bytes)
            print("send_seq_no=", self.seq_no, "data_bytes", len(data_bytes), "ack=", self.ack)
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))

        while self.ack == 0:
            time.sleep(0.01)
            if time.time() - send_time > self.time_out:
                print("retransmit: ", self.seq_no)
                self.send(data_bytes)
                return
        self.ack = 0
        self.seq_no += 1
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
            self.remove_key = []
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
        send_time = time.time()
        while self.ack == 0:
            time.sleep(0.01)
            self.fin = 1
            if time.time() - send_time > self.time_out:
                print("retransmit fin: ", self.seq_no)
                self.send(b"")
                return
        self.closed = True
        self.socket.stoprecv()
        pass

    def check_corruption(self, data_bytes, recv_checksum):
        return recv_checksum == self.format_checksum(hashlib.sha224(data_bytes).hexdigest())

    def listener(self):
        while not self.closed:  # a later hint will explain self.closed
            try:
                data, addr = self.socket.recvfrom()
                if len(data) == 0:
                    return data
                # store the data in the receive buffer
                packet = struct.unpack('i i i i H' + str(len(data) - 18) + 's', data)
                header = struct.pack(('i i i i' + str(len(packet[5])) + 's'),
                                     packet[0], packet[1], packet[2], packet[3], packet[5])
                if not self.check_corruption(header, packet[4]):
                    print("check_corruption failed, checksum = ", packet[4])
                    continue
                recv_seq_no = packet[0]
                if packet[2] > self.ack_no:
                    self.ack_no = packet[2]
                recv_checksum = packet[4]
                print("check_sum", recv_checksum)
                recv_data = packet[5]
                if packet[1] and self.ack_no == self.seq_no:
                    self.ack = 1
                else:
                    self.ack = 0
                self.fin = packet[3]
                print("len of data: ", len(recv_data))
                if len(recv_data) <= 1:
                    self.next_seq_no = self.ack_no + 1
                    print("server side: seq_no :", recv_seq_no, "only ack received and ack==", self.ack)
                    if self.fin == 1 and self.ack == 1:
                        self.close()
                    elif self.fin == 1 and self.ack == 0:
                        self.ack = 1
                        self.send(b"")
                        self.close()
                    continue

                print("buffer size=", len(self.buffer), "buffer==", self.buffer)
                print("recv_seq_no=", recv_seq_no, "nextSeq_no=", self.next_seq_no, "ack_no=", self.ack_no)

                if recv_seq_no == self.next_seq_no:
                    # print("client ready to ack")
                    self.ack = 1
                    self.ack_no = recv_seq_no
                    self.seq_no = recv_seq_no
                    self.send(b'')

                elif recv_seq_no <= self.ack_no:
                    print("wrong retransmit here: recev:", recv_seq_no, "ack_no:", self.ack_no)
                    self.ack = 1
                    self.ack_no = recv_seq_no
                    self.seq_no = recv_seq_no
                    self.send(b'')
                    continue

                elif recv_seq_no >= self.ack_no + 1:  # ack lost
                    print("ack lost: recev:", recv_seq_no, "ack_no:", self.ack_no)
                    self.ack = 1
                    self.ack_no = recv_seq_no
                    self.seq_no = recv_seq_no
                    self.send(b'')
                    continue

                # store the data in the receive buffer
                self.buffer[recv_seq_no] = recv_data

            except Exception as e:
                print(" listener died !")
                print(e)
