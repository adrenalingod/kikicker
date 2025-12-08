# bla.py
import threading
import time
import subprocess
from bla_buffer import BLAData

class BLAAdvertiser:
    def __init__(self, interval=1):
        self.interval = interval
        self.running = False
        self.thread = None

        # BLE header for Legacy ADV
        self.header = bytes.fromhex(
            "020106"            # flags (Length:2, Type:01 "Flags", Data:06 "LE General Discoverable")
            "09"                # Name Length
            "09"                # Name Type 9 = ASCII
            "6b696b69636b6572"  # Name in Hex ASCII "kikicker"
        )
        # max BLE payload: 31 - len(header)
        self.max_payload = 31 - len(self.header)
        print(self.max_payload)

    # ------------------------------------------------------------

    def _build_packet(self):
        # BLAData.consume_for_packet now returns a packed payload (bytes)
        payload = BLAData.consume_for_packet(self.max_payload)
        return self.header #+ payload

    # ------------------------------------------------------------

    def _send_packet(self, packet):
        """
        Send BLE raw advertising packet using hcitool.
        Uses timeout so it NEVER blocks.
        """

        # 1. Convert the bytes object 'packet' to a hex string
        hexdata = packet.hex()
        # print(f"Raw hexdata: {hexdata}")

        # 2. Calculate the length of the payload in bytes (each byte is 2 hex chars)
        payload_length_bytes = len(hexdata) // 2

        # 3. Format the length as a two-character hex string (e.g., '1f' for 31 bytes)
        length_hex_str = format(payload_length_bytes, '02x')

        # 4. Slice the hex data string into a list of 2-character strings (['02', '01', '06', ...])
        payload_list = [hexdata[i:i+2] for i in range(0, len(hexdata), 2)]

        # 5. Construct the full command list, inserting the length byte in the correct position
        cmd = [
            "sudo", "hcitool", "-i", "hci0",
            "cmd", "0x08", "0x0008",
            length_hex_str
        ] + payload_list
        
        # Command Print
        # print(f"Executing command: {' '.join(cmd)}")

        try:
            # Use subprocess.run to execute the command with a timeout
            subprocess.run(
                cmd,
                timeout=0.05,
                stdout=subprocess.DEVNULL,  # Suppress normal output
                stderr=subprocess.DEVNULL,  # Suppress error output
                check=True # Raise exception if command fails
            )
            cmd2 = "sudo", "hcitool", "-i", "hci0", "cmd", "0x08", "0x000a", "01"
            subprocess.run(
                cmd2,
                timeout=0.05,
                stdout=subprocess.DEVNULL,  # Suppress normal output
                stderr=subprocess.DEVNULL,  # Suppress error output
                check=True # Raise exception if command fails
            )
            
        except subprocess.TimeoutExpired:
            # This is expected behavior as hcitool might block slightly
            # print("hcitool command timed out (expected).")
            pass
        except subprocess.CalledProcessError as e:
            # Handle cases where hcitool fails, e.g., 'no device found'
            print(f"hcitool command failed: {e}")
        except FileNotFoundError:
            print("Error: 'hcitool' command not found. Ensure BlueZ is installed.")


    # ------------------------------------------------------------

    def _loop(self):
        while self.running:
            packet = self._build_packet()

            self._send_packet(packet)
            time.sleep(self.interval)


    # ------------------------------------------------------------

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)


# testing
#adv = BLAAdvertiser()
#try:
#    print("Starting advertiser. Press Ctrl+C to stop.")
#    adv.start()
#    # Keep the main thread alive until user interruption (Ctrl+C)
#    while True:
#        time.sleep(1)
#
#except KeyboardInterrupt:
#    # Handle the graceful shutdown when the user presses Ctrl+C
#    print("\nCtrl+C received. Stopping advertiser...")
#    pass
#
#finally:
#    # Ensure stop() is called to clean up threads properly
#    adv.stop()
#    print("Advertiser stopped. Exiting.")
