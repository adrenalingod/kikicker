class Bounce:
    def __init__(self, x_coord=0, y_coord=0, speed=0, frame_number=0):
        self.x_coord = x_coord  # 8 bits
        self.y_coord = y_coord  # 7 bits
        self.speed = speed      # 8 bits
        self.frame_number = frame_number  # 7 bits  30 bits total

    def to_bytes(self) -> bytes:
        """Convert bounce data to 4 bytes."""
        # Pack bits into a single integer
        packed = ((self.x_coord & 0xFF) << 22) | \
                 ((self.y_coord & 0x7F) << 15) | \
                 ((self.speed & 0xFF) << 7) | \
                 (self.frame_number & 0x7F)
        return packed.to_bytes(4, byteorder='big')

class BLA_Payload:
    def __init__(self):
        self.score_team_1 = 0  # 4 bits
        self.score_team_2 = 0  # 4 bits
        self.bounces = []  # list of bounces (4 max) 6bit left


    def add_bounce(self, bounce: Bounce):
        if len(self.bounces) >= 4:
            raise ValueError('Maximum of 4 bounces allowed')
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
        """Convert the entire payload to bytes and consume the bounces."""
        # First byte: 4 bits score team 1, 4 bits score team 2
        first_byte = ((self.score_team_1 & 0x0F) << 4) | (self.score_team_2 & 0x0F)
        payload_bytes = bytearray([first_byte])
        
        # Add bounce data
        for bounce in self.bounces:
            if isinstance(bounce, Bounce):
                payload_bytes.extend(bounce.to_bytes())
            else:
                raise ValueError('Invalid bounce data')
        self.clear_bounces()  # Clear bounces after converting to bytes
        if self.score_team_1 >= 10  or self.score_team_2 >= 10:
            print("Scores reached 10, Game has ended, resetting scores")
            self.clear_goals()

        payload = bytes(payload_bytes)
        return payload

    @staticmethod
    def decode_payload(payload: bytes) -> str:
        """Produce a human-readable summary from the raw payload bytes."""
        if not payload:
            return 'Empty payload'

        team1 = (payload[0] >> 4) & 0x0F
        team2 = payload[0] & 0x0F
        summary = [f'Score: {team1}:{team2}']

        for idx, offset in enumerate(range(1, len(payload), 4), start=1):
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
        payload.team2_scored()
        payload.team2_scored()
        payload.team2_scored()
        payload.team2_scored()
        payload.team2_scored()
        payload.team2_scored()
        payload.add_bounce(Bounce(120, 10, 13, 5))
        payload.add_bounce(Bounce(10, 50, 6, 2))
        payload.add_bounce(Bounce(10, 50, 6, 2))
        payload.add_bounce(Bounce(10, 50, 6, 2))
        data = payload.to_bytes()
        print('Encoded payload:', data.hex())
        print('Decoded view:', BLA_Payload.decode_payload(data))


if __name__ == '__main__':
    BLA_PayloadTester.run_demo()

