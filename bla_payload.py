class Bounce:
    def __init__(self, x_coord=0, y_coord=0, speed=0, frame_number=0):
        self.x_coord = x_coord  # 8 bits
        self.y_coord = y_coord  # 7 bits
        self.speed = speed      # 8 bits
        self.frame_number = frame_number  # 7 bits
        # Total: 30 bits (packed into 4 bytes, 2 bits unused)

    def to_bytes(self) -> bytes:
        """Convert bounce data to 4 bytes."""
        # Pack bits into a single integer (30 bits used, 2 bits unused)
        packed = ((self.x_coord & 0xFF) << 22) | \
                 ((self.y_coord & 0x7F) << 15) | \
                 ((self.speed & 0xFF) << 7) | \
                 (self.frame_number & 0x7F)
        return packed.to_bytes(4, byteorder='big')

class BLA_Payload:
    def __init__(self):
        self.score_team_1 = 0  # 4 bits
        self.score_team_2 = 0  # 4 bits
        self.ball_possession = 0  # 1 bit (0 = team1, 1 = team2)
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

    def set_team1_ball_possession(self):
        self.ball_possession = 0
    
    def set_team2_ball_possession(self):
        self.ball_possession = 1

    def to_bytes(self) -> bytes:
        """Convert the entire payload to bytes and consume the bounces.
        
        Byte layout:
        - Byte 0: [4 bits team1 score][4 bits team2 score]
        - Byte 1: [1 bit possession][7 bits reserved/unused]
        - Bytes 2-5: Bounce 1 (4 bytes)
        - Bytes 6-9: Bounce 2 (4 bytes)
        - Bytes 10-13: Bounce 3 (4 bytes)
        Total: 14 bytes max
        """
        # First byte: 4 bits score team 1, 4 bits score team 2
        first_byte = ((self.score_team_1 & 0x0F) << 4) | (self.score_team_2 & 0x0F)
        
        # Second byte: 1 bit possession, 7 bits unused (could be used for future features)
        second_byte = (self.ball_possession & 0x01) << 7
        
        payload_bytes = bytearray([first_byte, second_byte])
        
        # Add bounce data
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
        
        if len(payload) < 2:
            return f'Invalid payload (too short: {len(payload)} bytes)'

        # Decode scores from first byte
        team1 = (payload[0] >> 4) & 0x0F
        team2 = payload[0] & 0x0F
        
        # Decode possession from second byte
        possession = (payload[1] >> 7) & 0x01
        possession_str = "Team2" if possession else "Team1"
        
        summary = [f'Score: {team1}:{team2}', f'Possession: {possession_str}']

        # Decode bounces (starting from byte 2)
        for idx, offset in enumerate(range(2, len(payload), 4), start=1):
            if offset + 4 > len(payload):
                summary.append(f'Bounce{idx} <truncated data>')
                break
            chunk = payload[offset:offset + 4]
            value = int.from_bytes(chunk, byteorder='big')
            x_coord = (value >> 22) & 0xFF
            y_coord = (value >> 15) & 0x7F
            speed = (value >> 7) & 0xFF
            frame_number = value & 0x7F
            summary.append(
                f'Bounce{idx} x:{x_coord} y:{y_coord} speed:{speed} frame:{frame_number}'
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
        payload.set_team2_ball_possession()
        payload.add_bounce(Bounce(120, 10, 13, 5))
        payload.add_bounce(Bounce(10, 50, 6, 2))
        payload.add_bounce(Bounce(85, 63, 15, 120))
        
        data = payload.to_bytes()
        print('Encoded payload:', data.hex())
        print('Payload size:', len(data), 'bytes')
        print('Decoded view:', BLA_Payload.decode_payload(data))
        
        # Test with only scores
        payload2 = BLA_Payload()
        payload2.team1_scored()
        payload2.team1_scored()
        payload2.team1_scored()
        payload2.set_team1_ball_possession()
        data2 = payload2.to_bytes()
        print('\nScores only payload:', data2.hex())
        print('Payload size:', len(data2), 'bytes')
        print('Decoded view:', BLA_Payload.decode_payload(data2))


if __name__ == '__main__':
    BLA_PayloadTester.run_demo()

