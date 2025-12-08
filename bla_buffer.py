# bla_buffer.py
import threading
from collections import deque


class Bounce:
    __slots__ = ("angle", "speed", "frame", "quad")

    def __init__(self, angle, speed, frame, quad):
        self.angle = angle & 0xFF
        self.speed = speed & 0xFF
        self.frame = frame & 0x7F
        self.quad = quad & 0x0F


class BLAData:
    """
    Global buffer accessible from main.
    Thread-safe.
    """
    lock = threading.Lock()

    # persistent goal info
    _goal_player = 0
    _goal_counter = 0   # how many cycles left to keep it

    # current initial coordinate
    _initial_x = 0
    _initial_y = 0

    # queue of pending bounces
    _bounces = deque()

    @staticmethod
    def set_initial_coord(x, y):
        with BLAData.lock:
            BLAData._initial_x = x & 0x7F
            BLAData._initial_y = y & 0x3F

    @staticmethod
    def push_goal(player_id):
        """
        1 = left player scored
        2 = right player scored
        """
        with BLAData.lock:
            BLAData._goal_player = player_id & 0x03
            BLAData._goal_counter = 5  # keep for 5 advertising cycles

    @staticmethod
    def add_bounce(bounce):
        with BLAData.lock:
            BLAData._bounces.append(bounce)

    @staticmethod
    def consume_for_packet(max_payload_bytes):
        """
        Build a bit-packed payload from the global buffer according to the
        BLA specification:

        - 2 bits: goal (0=no goal, 1=left, 2=right)
        - 7 bits: initial X (0..127)
        - 6 bits: initial Y (0..63)
        - For each bounce (until payload full):
            - 8 bits angle
            - 8 bits speed
            - 7 bits frame
            - 4 bits quadrant

        The function consumes as many bounces from the deque as fit into
        `max_payload_bytes` and returns the packed payload bytes.
        """
        with BLAData.lock:
            # goal bits decay
            goal_bits = BLAData._goal_player
            if BLAData._goal_counter > 0:
                BLAData._goal_counter -= 1
                if BLAData._goal_counter == 0:
                    BLAData._goal_player = 0

            init_x = BLAData._initial_x & 0x7F
            init_y = BLAData._initial_y & 0x3F

            # Bit-accumulator (MSB-first)
            acc = 0
            bits = 0

            def append_bits(value: int, nbits: int):
                nonlocal acc, bits
                acc = (acc << nbits) | (value & ((1 << nbits) - 1))
                bits += nbits

            # Append header fields
            append_bits(goal_bits & 0x03, 2)
            append_bits(init_x, 7)
            append_bits(init_y, 6)

            # Helper to compute current byte length if we append extra bits
            def byte_length_if(extra_bits: int) -> int:
                total = bits + extra_bits
                pad = (8 - (total % 8)) % 8
                return (total + pad) // 8

            # Collect how many bounces we will consume
            to_consume = 0
            # Iterate over bounces without popping; check if each fits
            for b in list(BLAData._bounces):
                extra = 8 + 8 + 7 + 4  # 27 bits per bounce
                if byte_length_if(extra) <= max_payload_bytes:
                    # accept this bounce
                    append_bits(b.angle & 0xFF, 8)
                    append_bits(b.speed & 0xFF, 8)
                    append_bits(b.frame & 0x7F, 7)
                    append_bits(b.quad & 0x0F, 4)
                    to_consume += 1
                else:
                    break

            # Actually pop the consumed bounces from the deque
            for _ in range(to_consume):
                BLAData._bounces.popleft()

            # Pad to full bytes (MSB-first)
            pad = (8 - (bits % 8)) % 8
            if pad:
                acc = acc << pad
                bits += pad

            total_bytes = bits // 8
            if total_bytes == 0:
                return bytes()
            payload = acc.to_bytes(total_bytes, byteorder='big')
            return payload
