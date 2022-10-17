# do not import anything else from loss_socket besides LossyUDP
import struct

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
        self.buffer = {}
        self.remove_key = []

    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!
        while len(data_bytes) > 1468:
            tmp_bytes = data_bytes[0:1468]
            packet = struct.pack('i ' + str(len(tmp_bytes)) + 's', self.seq_no, tmp_bytes)
            # print("send_seq_no=", self.seq_no, "tmp_bytes", len(tmp_bytes), "tmp_bytes=", tmp_bytes)
            data_bytes = data_bytes[1468:]
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            self.seq_no += 1

        # for now I'm just sending the raw application-level data in one UDP payload
        if len(data_bytes) > 0:
            packet = struct.pack('i' + str(len(data_bytes)) + 's', self.seq_no, data_bytes)
            # print("send_seq_no=", self.seq_no, "data_bytes", len(data_bytes), "data_bytes=", data_bytes)
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            self.seq_no += 1

    def process_dict_packets(self, multiple_output):
        for key, val in self.buffer.items():
            if key == self.next_seq_no:
                # print("seq num matches", key)
                self.next_seq_no += 1
                self.remove_key.append(key)
                multiple_output += val

        if multiple_output != b"":
            if len(self.remove_key) != 0:
                for _, val in enumerate(self.remove_key):
                    self.buffer.pop(val)
            self.remove_key = []
            # print("dict info ====", self.buffer.keys())
            return multiple_output
        return b""

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        # your code goes here!  The code below should be changed!
        chunks = b''
        data, _ = self.socket.recvfrom()
        if len(data) == 0:
            return data

        packet = struct.unpack('i ' + str(len(data) - 4) + 's', data)
        recv_seq_no = packet[0]
        recv_data = packet[1]
        # print("recv_seq_no=", recv_seq_no, "recv_data=", recv_data)

        # print("dict now =", self.buffer)
        if recv_seq_no != self.next_seq_no:
            self.buffer[recv_seq_no] = recv_data
            # print("recv_seq_no != next_seq_no, received=", recv_seq_no, "expected=", self.next_seq_no)
            return self.process_dict_packets(b"")
        else:
            # print("recv_seq_no == next_seq_no, received=", recv_seq_no, "expected=", self.next_seq_no)
            # print("dict info ====", self.buffer.keys())
            self.next_seq_no += 1
            return self.process_dict_packets(recv_data)
        # this sample code just calls the recvfrom method on the LossySocket
        # For now, I'll just pass the full UDP payload to the app

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        pass
