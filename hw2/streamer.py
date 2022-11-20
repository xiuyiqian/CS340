# do not import anything else from loss_socket besides LossyUDP
import struct
import time
from concurrent.futures import ThreadPoolExecutor
import hashlib
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY

chunk_size = 1454

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
        self.fin = 0
        self.checksum = None

        self.time_out = 0.25  # threshold value
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

    def format_packet(self, data_bytes):
        header = struct.pack(('i i i i' + str(len(data_bytes)) + 's'),
                             self.seq_no, self.ack, self.ack_no, self.fin, data_bytes)
        self.checksum = self.format_checksum(hashlib.sha224(header).hexdigest())
        packet = struct.pack('i i i i H' + str(len(data_bytes)) + 's',
                             self.seq_no, self.ack, self.ack_no, self.fin, self.checksum, data_bytes)
        # print("send_seq_no=", self.seq_no, "data_bytes", len(data_bytes), "data_bytes=", data_bytes)
        return packet

    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""

        chunk_index = 0
        while chunk_size*chunk_index < len(data_bytes):
            if (chunk_index+1) * chunk_size < len(data_bytes):
                tmp_bytes = data_bytes[chunk_size*chunk_index: (chunk_index+1) * chunk_size]

            else:
                tmp_bytes = data_bytes[chunk_size*chunk_index:]
            print("inside while send_seq_no=", self.seq_no, "data_bytes", tmp_bytes, "ack=", self.ack)
            # packet = struct.pack('i i i i' + str(len(tmp_bytes)) + 's', self.seq_no, self.ack, self.ack_no, self.fin, tmp_bytes)

            packet = self.format_packet(tmp_bytes)
            self.send_buffer[self.seq_no] = (time.time(), packet)
            send_time = time.time()
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))


            while self.ack == 0 or self.ack_no != self.seq_no:
                time.sleep(0.01)
                if time.time() - send_time > self.time_out:
                    print("retransmit: ", self.seq_no)
                    self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                if self.ack and self.ack_no == self.seq_no:
                    self.seq_no = self.ack_no + 1
                    break

            chunk_index += 1
            self.ack = 0

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        # your code goes here!  The code below should be changed!
        multiple_output = b""
        while self.buffer.get(self.next_seq_no):
            key = self.next_seq_no
            val = self.buffer[self.next_seq_no]
            self.next_seq_no += 1
            self.seq_no += 1
            print("seq num matches", key, "next_seq_no", self.next_seq_no)
            self.buffer.pop(key)
            multiple_output += val

        return multiple_output

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.

        if self.fin == 0:
            while self.ack == 0 or self.ack_no != -1:
                time.sleep(0.01)
                send_time = time.time()
                self.send_fin()
                if time.time() - send_time > self.time_out:
                    print("retransmit fin: ", self.seq_no)
                    self.send_fin()

        self.ack = 0
        self.closed = True
        self.socket.stoprecv()

    def send_fin(self):
        self.fin = 1
        self.seq_no = -1
        tmp_bytes = b""
        self.ack = 0
        print("send fin message")
        packet = self.format_packet(tmp_bytes)
        self.socket.sendto(packet, (self.dst_ip, self.dst_port))

    def send_ack(self):
        tmp_bytes = b""
        self.ack = 1
        packet = self.format_packet(tmp_bytes)
        self.socket.sendto(packet, (self.dst_ip, self.dst_port))
        self.ack = 0

    def check_corruption(self, packet, recv_checksum):
        header = struct.pack(('i i i i' + str(len(packet[5])) + 's'),
                             packet[0], packet[1], packet[2], packet[3], packet[5])
        return recv_checksum == self.format_checksum(hashlib.sha224(header).hexdigest())

    def listener(self):
        while not self.closed:  # a later hint will explain self.closed
            try:
                data, addr = self.socket.recvfrom()
                if len(data) == 0:
                    self.closed = True
                # store the data in the receive buffer
                packet = struct.unpack('i i i i H' + str(len(data) - 18) + 's', data)
                if not self.check_corruption(packet, packet[4]):
                    print("check_corruption failed, checksum = ", packet[4])
                    continue
                recv_seq_no = packet[0]
                self.ack_no = packet[2]
                self.fin = packet[3]
                recv_data = packet[5]
                self.ack = packet[1]
                print("len of data: ", len(recv_data))
                if self.seq_no == -1 and self.fin == 1:
                    print("receive fin message")
                    if self.ack == 0:
                        print("send fin ack message")
                        self.ack_no = -1
                        self.send_ack()
                        continue
                    else:
                        print("receive fin ack message")
                        self.fin = 1
                        self.closed = True
                        continue

                if len(recv_data) <= 1:
                    self.next_seq_no = self.ack_no+1
                    print("server side: only ack received and ack==", self.ack)
                    continue

                print("recv_seq_no=", recv_seq_no, "recv_data=", recv_data, "ack is=", self.ack)
                print("recv_seq_no=", recv_seq_no, "nextSeq_no=", self.next_seq_no)

                if recv_seq_no == self.next_seq_no:
                    # print("client ready to ack")
                    self.ack = 1
                    self.ack_no = recv_seq_no
                    self.seq_no = recv_seq_no
                    self.send_ack()
                    print("here")
                elif recv_seq_no < self.next_seq_no:
                    self.ack = 1
                    self.ack_no = recv_seq_no
                    self.seq_no = self.next_seq_no
                    self.send_ack()
                    print("or here")
                    continue

                if self.buffer.get(recv_seq_no):
                    continue
                self.buffer[recv_seq_no] = recv_data
                # print("buffer size=", len(self.buffer), "buffer==", self.buffer)

            except Exception as e:
                print(" listener died !")
                print(e)

