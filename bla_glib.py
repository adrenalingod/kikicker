"""GLib-based HCI advertiser using GLib's event loop for timing.

Uses GLib main loop for precise timing without busy-waiting.
Can achieve consistent sub-10ms intervals with minimal CPU overhead.

Requires: pygobject, libglib2.0
"""
import struct
import socket
import threading
from gi.repository import GLib


class BLAAdvertiserGLib:
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
        self.main_loop = None
        self.timeout_id = None

        # Build basic AD elements
        self.flags_ad = bytes.fromhex("020106")
        self.name = b'kikicker'
        self.name_ad = bytes([len(self.name) + 1, 0x09]) + self.name
        self.base_header = self.flags_ad + self.name_ad

    def _open_socket(self):
        try:
            self.sock = socket.socket(socket.AF_BLUETOOTH,
                                      socket.SOCK_RAW,
                                      socket.BTPROTO_HCI)
        except AttributeError:
            raise RuntimeError('Python socket does not support AF_BLUETOOTH/BTPROTO_HCI')
        self.sock.setblocking(True)
        self.sock.bind((self.dev_id,))

    def _close_socket(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def _opcode(self, ogf, ocf):
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

    def _set_advertise_enable(self, enable: bool):
        """Enable/disable advertising."""
        val = b'\x01' if enable else b'\x00'
        self._hci_send_cmd(0x08, 0x000A, val)

    def _build_packet(self):
        """Build packet."""
        return self.base_header

    def _advertise_callback(self):
        """Called by GLib timer to send advertisement."""
        if self.running:
            try:
                packet = self._build_packet()
                self._set_advertising_data(packet)
            except Exception:
                pass
            
            # Re-schedule with precise interval (in milliseconds)
            self.timeout_id = GLib.timeout_add(int(self.interval * 1000), self._advertise_callback)
        
        return False  # Don't repeat through GLib callback

    def _glib_loop(self):
        """Run GLib main loop in thread."""
        self.main_loop = GLib.MainLoop()
        
        # Set up initial timer
        self.timeout_id = GLib.timeout_add(int(self.interval * 1000), self._advertise_callback)
        
        try:
            self.main_loop.run()
        except KeyboardInterrupt:
            pass

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
        
        # Now enable advertising on controller
        try:
            self._set_advertise_enable(True)
            print('Advertising enabled on controller')
        except Exception as e:
            print(f'Failed to enable advertising: {e}')
            raise
        
        self.running = True
        self.thread = threading.Thread(target=self._glib_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop advertising."""
        self.running = False
        
        if self.main_loop:
            try:
                self.main_loop.quit()
            except Exception:
                pass
        
        if self.thread:
            self.thread.join(timeout=1.0)
        
        try:
            self._set_advertise_enable(False)
        except Exception:
            pass
        
        self._close_socket()


if __name__ == '__main__':
    adv = BLAAdvertiserGLib(interval=0.005)
    try:
        print('Starting GLib advertiser (requires root).')
        print('Using GLib main loop for timing (5ms interval)')
        adv.start()
        
        import time
        while True:
            time.sleep(5)
            stats = adv.get_stats()
            print(f'Packets sent: {stats["packets_sent"]}')
            
    except KeyboardInterrupt:
        pass
    finally:
        adv.stop()
