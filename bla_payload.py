class Bounce:
    def __init__(self, x_coord=0, y_coord=0, speed=0, frame_number=0, ball_possession=0):
        self.x_coord = x_coord  # 8 bits
        self.y_coord = y_coord  # 7 bits
        self.speed = speed      # 8 bits
        self.frame_number = frame_number  # 7 bits
        self.ball_possession = ball_possession  # 1 bit (0 = team1, 1 = team2)
        # Total: 31 bits (packed into 4 bytes, 1 bit unused)

    def to_bytes(self) -> bytes:
        """Convert bounce data to 4 bytes."""
        # Pack bits into a single integer (31 bits used, 1 bit unused)
        packed = ((self.x_coord & 0xFF) << 23) | \
                 ((self.y_coord & 0x7F) << 16) | \
                 ((self.speed & 0xFF) << 8) | \
                 ((self.frame_number & 0x7F) << 1) | \
                 (self.ball_possession & 0x01)
        return packed.to_bytes(4, byteorder='big')

class BLA_Payload:
    def __init__(self):
        self.score_team_1 = 0  # 4 bits
        self.score_team_2 = 0  # 4 bits
        self.bounces = []  # list of bounces (3 max to fit in 14 bytes)

    def add_bounce(self, bounce: Bounce):
        if len(self.bounces) >= 3:
            raise ValueError('Maximum of 3 bounces allowed (14 byte limit)')
        self.bounces.append(bounce)

    def clear_bounces(self):
        self.bounces = []

    def team1_scored(self):
        self.score_team_1 += 1
    
    def team2_scored(self):
        self.score_team_2 += 1  

    def clear_goals(self):
        self.score_team_1 = 0
        self.score_team_2 = 0

    def to_bytes(self) -> bytes:
        """Convert the entire payload to bytes and consume the bounces.
        
        Byte layout:
        - Byte 0: [4 bits team1 score][4 bits team2 score]
        - Bytes 1-4: Bounce 1 (4 bytes, includes possession bit)
        - Bytes 5-8: Bounce 2 (4 bytes, includes possession bit)
        - Bytes 9-12: Bounce 3 (4 bytes, includes possession bit)
        - Byte 13: Reserved/unused (for future use)
        Total: 14 bytes max
        """
        # First byte: 4 bits score team 1, 4 bits score team 2
        first_byte = ((self.score_team_1 & 0x0F) << 4) | (self.score_team_2 & 0x0F)
        
        payload_bytes = bytearray([first_byte])
        
        # Add bounce data (each bounce now includes possession bit)
        for bounce in self.bounces:
            if isinstance(bounce, Bounce):
                payload_bytes.extend(bounce.to_bytes())
            else:
                raise ValueError('Invalid bounce data')
        
        self.clear_bounces()  # Clear bounces after converting to bytes
        
        if self.score_team_1 >= 10 or self.score_team_2 >= 10:
            print("Scores reached 10, Game has ended, resetting scores")
            self.clear_goals()

        payload = bytes(payload_bytes)
        return payload

    @staticmethod
    def decode_payload(payload: bytes) -> str:
        """Produce a human-readable summary from the raw payload bytes."""
        if not payload:
            return 'Empty payload'
        
        if len(payload) < 1:
            return f'Invalid payload (too short: {len(payload)} bytes)'

        # Decode scores from first byte
        team1 = (payload[0] >> 4) & 0x0F
        team2 = payload[0] & 0x0F
        
        summary = [f'Score: {team1}:{team2}']

        # Decode bounces (starting from byte 1, each bounce is 4 bytes)
        for idx, offset in enumerate(range(1, len(payload), 4), start=1):
            if offset + 4 > len(payload):
                summary.append(f'Bounce{idx} <truncated data>')
                break
            chunk = payload[offset:offset + 4]
            value = int.from_bytes(chunk, byteorder='big')
            x_coord = (value >> 23) & 0xFF
            y_coord = (value >> 16) & 0x7F
            speed = (value >> 8) & 0xFF
            frame_number = (value >> 1) & 0x7F
            possession = value & 0x01
            possession_str = "T2" if possession else "T1"
            summary.append(
                f'Bounce{idx} x:{x_coord} y:{y_coord} speed:{speed} frame:{frame_number} pos:{possession_str}'
            )

        return ' '.join(summary)


class BLA_PayloadTester:
    """Simple test harness to simulate payload creation and decoding."""

    @staticmethod
    def run_demo():
        payload = BLA_Payload()
        payload.team1_scored()
        payload.team2_scored()
        payload.team2_scored()
        payload.add_bounce(Bounce(120, 10, 13, 5, ball_possession=0))  # Team 1 has ball
        payload.add_bounce(Bounce(10, 50, 6, 2, ball_possession=1))    # Team 2 has ball
        payload.add_bounce(Bounce(85, 63, 15, 120, ball_possession=1)) # Team 2 has ball
        
        data = payload.to_bytes()
        print('Encoded payload:', data.hex())
        print('Payload size:', len(data), 'bytes')
        print('Decoded view:', BLA_Payload.decode_payload(data))
        
        # Test with only scores
        payload2 = BLA_Payload()
        payload2.team1_scored()
        payload2.team1_scored()
        payload2.team1_scored()
        data2 = payload2.to_bytes()
        print('\nScores only payload:', data2.hex())
        print('Payload size:', len(data2), 'bytes')
        print('Decoded view:', BLA_Payload.decode_payload(data2))


if __name__ == '__main__':
    BLA_PayloadTester.run_demo()

