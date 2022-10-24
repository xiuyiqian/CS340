# do not import anything else from loss_socket besides LossyUDP
import struct
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
import threading
from contextlib import contextmanager

max_packet_len = 1454


class TimeoutLock(object):
    def __init__(self):
        self._lock = threading.Lock()

    def acquire(self, blocking=True, timeout=-1):
        return self._lock.acquire(blocking, timeout)

    @contextmanager
    def acquire_timeout(self, timeout):
        result = self._lock.acquire(timeout=timeout)
        yield result
        if result:
            self._lock.release()

    def release(self):
        self._lock.release()

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
        self.send_buffer = {}

        self.time_out = 0.1  # threshold value
        self.retransmission = False
        self.lock = TimeoutLock()

        self.executor = ThreadPoolExecutor(max_workers=2)
        self.executor.submit(self.listener)

    # get online
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
        print("send_seq_no=", self.seq_no, "data_bytes", len(data_bytes), "data_bytes=", data_bytes)

        # put into sender buffer, key: seq_No, val: (data, send_time)
        self.socket.sendto(packet, (self.dst_ip, self.dst_port))

    def send_inflight_packet(self):
        while not self.closed:
            if self.next_seq_no < len(self.send_buffer):
                self.seq_no = self.next_seq_no
                data_bytes = self.send_buffer[self.next_seq_no][0]

                while len(data_bytes) >= max_packet_len:
                    tmp_bytes = data_bytes[0:max_packet_len]
                    self.format_packet(tmp_bytes)
                    data_bytes = data_bytes[max_packet_len:]
                    self.seq_no += 1
                    self.next_seq_no += 1

                if len(data_bytes) >= 0:
                    self.format_packet(data_bytes)
                    self.seq_no += 1

                self.next_seq_no += 1

            # receive ack:
            if self.ack_no+1 == self.next_seq_no:
                continue
            else:
                if time.time() - self.send_buffer[self.ack_no][1] > self.time_out:
                    self.next_seq_no = self.ack_no + 1
                    print("retransmit since last ack_no+1 ", self.next_seq_no)
                    self.send_inflight_packet()
                    return

                print("go here")

    def send_ack(self, data_bytes):
        send_time = time.time()
        if len(data_bytes) >= 0:
            self.format_packet(data_bytes)

    def deal_with_send_buffer(self):
        while len(self.send_buffer) != 0:
            self.send_inflight_packet()


    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!
        send_time = time.time()
        # print("original data_bytes", data_bytes)
        self.send_buffer[len(self.send_buffer)] = (data_bytes, send_time)
        print("send buffer size=", len(self.send_buffer))
        self.executor.submit(self.deal_with_send_buffer)

    def process_dict_packets(self, multiple_output):
        # print("next_seq_no=", self.next_seq_no)
        for key, val in self.buffer.copy().items():  # since multithreading, we need to make copy while we iterate through
            if key == self.next_seq_no:
                self.next_seq_no += 1
                print("seq num matches", key, "next_seq_no", self.next_seq_no, "val=", val)
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

    def check_corruption(self, packet, recv_checksum):
        header = struct.pack(('i i i i' + str(len(packet[5])) + 's'),
                             packet[0], packet[1], packet[2], packet[3], packet[5])
        return recv_checksum == self.format_checksum(hashlib.sha224(header).hexdigest())

    def listener(self):
        while not self.closed:  # a later hint will explain self.closed
            try:
                data, addr = self.socket.recvfrom()
                if len(data) == 0:
                    return data
                # store the data in the receive buffer
                packet = struct.unpack('i i i i H' + str(len(data) - 18) + 's', data)
                if not self.check_corruption(packet, packet[4]):
                    print("check_corruption failed, checksum = ", packet[4])
                    continue
                recv_seq_no = packet[0]
                if packet[2] > self.ack_no:
                    self.ack_no = packet[2]
                # recv_checksum = packet[4]
                # # print("check_sum", recv_checksum)
                recv_data = packet[5]
                self.ack = packet[1]
                self.fin = packet[3]
                # print("len of data: ", len(recv_data))

                # deal with only ack packet
                if len(recv_data) <= 1:
                    self.next_seq_no = self.ack_no + 1
                    self.seq_no = self.ack_no + 1
                    print("server side ack_no: seq_no :", self.ack_no, "only ack received and ack==", self.ack)
                    continue

                # print("buffer size=", len(self.buffer), "buffer==", self.buffer)
                # print("recv_seq_no=", recv_seq_no, "recv_data=", recv_data, "nextSeq_no=", self.next_seq_no, "ack_no=", self.ack_no)

                if recv_seq_no == self.next_seq_no:
                    self.ack = 1
                    self.ack_no = recv_seq_no
                    self.seq_no = recv_seq_no
                    self.send_ack(b"")

                else:
                    self.ack = 1
                    self.ack_no = self.next_seq_no - 1
                    self.send_ack(b"")
                    continue

                self.buffer[recv_seq_no] = recv_data

            except Exception as e:
                print(" listener died !")
                print(e)
