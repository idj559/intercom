#
# Intercom_minimal
# |
# +- Intercom_buffer
#    |
#    +- Intercom_bitplanes
#       |
#       +- Intercom_binaural
#          |
#          +- Intercom_DFC
#             |
#             +- Intercom_empty
#
# Don't send empty bitplanes.
#
# The sender of the bitplanes adds, to the number of received
# bitplanes, the number of skipped (zero) bitplanes of the chunk
# sent. We are also considered that the signs bitplane cound be all
# positives, something that could happen when we send a mono signal
# using two channels or the number of samples/chunk is very small.

import struct
import numpy as np
from intercom_minimal import Intercom_minimal
from intercom_dfc import Intercom_DFC

if __debug__:
    import sys

class Intercom_empty(Intercom_DFC):

    def init(self, args):
        Intercom_DFC.init(self, args)
        self.skipped_bitplanes = [0]*self.cells_in_buffer
        print("intercom_empty: ignoring 0-bitplanes")
        
    # Bitplanes are only sent if they have at least one bit to 1. If
    # the bitplane is not sent, we consider that it has been
    # transmitted for implementing the data-flow control.
    def send_bitplane(self, indata, bitplane_number):
        bitplane = (indata[:, bitplane_number%self.number_of_channels] >> bitplane_number//self.number_of_channels) & 1
        if np.any(bitplane): 
            bitplane = bitplane.astype(np.uint8)
            bitplane = np.packbits(bitplane)
            message = struct.pack(self.packet_format, self.recorded_chunk_number, bitplane_number, self.received_bitplanes_per_chunk[(self.played_chunk_number+1) % self.cells_in_buffer]+1, *bitplane)
            self.send_message(message)
            #self.sending_sock.sendto(message, (self.destination_address, self.destination_port))
        else:
            self.skipped_bitplanes[self.recorded_chunk_number % self.cells_in_buffer] += 1

    # The empty bitplanes are considered as transmitted (the rest of
    # the method is identical to the parent's one).
    def send(self, indata):
        #self.number_of_bitplanes_to_send = int(0.75*self.number_of_bitplanes_to_send + 0.25*self.number_of_received_bitplanes)
        #self.number_of_bitplanes_to_send = int(0.25*self.number_of_bitplanes_to_send)
        #self.number_of_bitplanes_to_send = int(0.75*self.number_of_bitplanes_to_send + 0.25*(self.number_of_sent_bitplanes - self.number_of_received_bitplanes)
        #self.number_of_bitplanes_to_send = self.number_of_received_bitplanes
        self.number_of_bitplanes_to_send = int(0.05*self.number_of_bitplanes_to_send + 0.95*self.number_of_received_bitplanes)
        self.number_of_bitplanes_to_send += self.skipped_bitplanes[(self.played_chunk_number+1) % self.cells_in_buffer]
        self.skipped_bitplanes[(self.played_chunk_number+1) % self.cells_in_buffer] = 0
        self.number_of_bitplanes_to_send += 1
        if self.number_of_bitplanes_to_send > self.max_number_of_bitplanes_to_send:
            self.number_of_bitplanes_to_send = self.max_number_of_bitplanes_to_send
        last_BPTS = self.max_number_of_bitplanes_to_send - self.number_of_bitplanes_to_send - 1  # last BitPlane To Send
        if __debug__:
            self._number_of_sent_bitplanes.value += (self.max_number_of_bitplanes_to_send - last_BPTS)
        #self.send_bitplane(indata, self.max_NOBPTS-1)
        #self.send_bitplane(indata, self.max_NOBPTS-2)
        #for bitplane_number in range(self.max_NOBPTS-3, last_BPTS, -1):
        #print("intercom_empty: ", self.max_number_of_bitplanes_to_send)
        for bitplane_number in range(self.max_number_of_bitplanes_to_send-1, last_BPTS, -1):
            self.send_bitplane(indata, bitplane_number)
        self.recorded_chunk_number = (self.recorded_chunk_number + 1) % self.CHUNK_NUMBERS

    # Volmeter of the received (played) audio.
    #def feedback(self):
    #    volume = "*"*(30-self.skipped_bitplanes[(self.played_chunk_number+1) % self.cells_in_buffer])
    #    sys.stderr.write(volume + '\n'); sys.stderr.flush()

if __name__ == "__main__":
    intercom = Intercom_empty()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()
