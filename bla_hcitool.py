"""Direct HCI-based BLE advertiser for fast advertising intervals.

Uses raw HCI socket commands to bypass BlueZ D-Bus restrictions.

Does the same thing as bla_glib.py but without GLib, using a simple thread and time.sleep for timing.
This is less precise than bla_glib.py but simpler and more portable (no GLib dependency

Was just used for testing and debugging, not the final choice for the project).
"""
import struct
import socket
import threading
import time


class BLAAdvertiserHCI:
    def __init__(self, device='hci0', interval=0.005):
        self.device = device
        try:
            self.dev_id = int(device.replace('hci', ''))
        except Exception:
            raise ValueError('device must be like "hci0"')
        self.interval = interval
        self.running = False
        self.thread = None
        self.sock = None
        self.last_log = 0.0
        self.custom_payload = b''

        # Build basic AD elements
        self.flags_ad = bytes.fromhex("020106")
        self.name = b'kikicker'
        self.name_ad = bytes([len(self.name) + 1, 0x09]) + self.name
        self.base_header = self.flags_ad + self.name_ad

    def _open_socket(self):
        """Open raw HCI socket."""
        try:
            self.sock = socket.socket(socket.AF_BLUETOOTH,
                                      socket.SOCK_RAW,
                                      socket.BTPROTO_HCI)
        except AttributeError:
            raise RuntimeError('Python socket does not support AF_BLUETOOTH/BTPROTO_HCI')
        self.sock.setblocking(True)
        self.sock.bind((self.dev_id,))

    def _close_socket(self):
        """Close HCI socket."""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def _opcode(self, ogf, ocf):
        """Calculate HCI opcode from OGF and OCF."""
        return (ocf & 0x03FF) | (ogf << 10)

    def _hci_send_cmd(self, ogf, ocf, params: bytes):
        """Send HCI command."""
        if not self.sock:
            raise RuntimeError('HCI socket not open')
        
        HCI_COMMAND_PKT = 0x01
        opcode = self._opcode(ogf, ocf)
        pkt = struct.pack('<BHB', HCI_COMMAND_PKT, opcode, len(params)) + params
        
        try:
            self.sock.send(pkt)
        except Exception:
            pass

    def _set_advertising_data(self, adv_data: bytes):
        """Set advertising data."""
        if len(adv_data) > 31:
            raise ValueError('Advertising data too long')
        plen = bytes([len(adv_data)])
        padded = adv_data + bytes(31 - len(adv_data))
        params = plen + padded
        self._hci_send_cmd(0x08, 0x0008, params)

    def _set_advertising_params(self):
        """Set advertising parameters."""
        # Convert interval from seconds to units of 0.625ms
        interval_units = int(self.interval / 0.000625)
        min_interval = max(0x0020, min(0x4000, interval_units))
        max_interval = min_interval
        
        params = struct.pack(
            '<HHBBB6sBB',
            min_interval,      # Min interval (2 bytes)
            max_interval,      # Max interval (2 bytes)
            0x03,              # ADV_NONCONN_IND (non-connectable, non-scannable)
            0x00,              # Own address type (public)
            0x00,              # Peer address type
            bytes(6),          # Peer address (not used)
            0x07,              # All channels
            0x00               # Filter policy
        )
        self._hci_send_cmd(0x08, 0x0006, params)
    
    def _set_advertise_enable(self, enable: bool):
        """Enable/disable advertising."""
        val = b'\x01' if enable else b'\x00'
        self._hci_send_cmd(0x08, 0x000A, val)

    def _build_packet(self):
        """Build packet."""
        return self.base_header + self.custom_payload

    def set_custom_payload(self, payload: bytes):
        """Set additional advertising payload as manufacturer-specific data."""
        company_id = 0x1337
        mfg_data = bytes([len(payload) + 3, 0xFF]) + company_id.to_bytes(2, 'little') + payload
        
        if len(self.base_header) + len(mfg_data) > 31:
            raise ValueError('Combined advertising payload exceeds 31 bytes')
        self.custom_payload = mfg_data

    def start(self):
        """Start advertising."""
        if self.running:
            return
        
        self._open_socket()
        
        # First, disable advertising to reset state
        try:
            self._set_advertise_enable(False)
            time.sleep(0.1)
        except Exception:
            pass
        
        # Set advertising parameters
        try:
            self._set_advertising_params()
        except Exception as e:
            raise
        
        # Set initial advertising data
        try:
            packet = self._build_packet()
            self._set_advertising_data(packet)
        except Exception as e:
            raise
        
        # Now enable advertising on controller
        try:
            self._set_advertise_enable(True)
        except Exception as e:
            raise
        
        self.running = True

    def stop(self):
        """Stop advertising."""
        self.running = False
        
        try:
            self._set_advertise_enable(False)
        except Exception:
            pass
        
        self._close_socket()


if __name__ == '__main__':
    from bla_payload import BLA_Payload, Bounce
    
    adv = BLAAdvertiserHCI(interval=0.005)
    payload = BLA_Payload()
    
    try:
        adv.start()
        
        counter = 0
        while True:
            # Create test payload
            payload.add_bounce(Bounce(counter % 255, (counter * 2) % 127, counter % 127, counter % 2))
            payload.add_bounce(Bounce(counter % 255, (counter * 2) % 127, counter % 127, counter % 2))
            payload.add_bounce(Bounce(counter % 255, (counter * 2) % 127, counter % 127, counter % 2))
            payload.add_bounce(Bounce(counter % 255, (counter * 2) % 127, counter % 127, counter % 2))
            
            if counter % 10 == 0:
                payload.team1_scored()
            if counter % 15 == 0:
                payload.team2_scored()
            
            data = payload.to_bytes()
            adv.set_custom_payload(data)
            
            # Update advertising data directly in main thread
            packet = adv._build_packet()
            adv._set_advertising_data(packet)
            
            now = time.time()
            if now - adv.last_log >= 0.1:
                print(f'Advertising payload: {packet.hex()}')
                adv.last_log = now
            
            counter = (counter + 1) & 0xFFFFFFFF
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        pass
    finally:
        adv.stop()
