import asyncio
import signal
import time
import argparse
from statistics import mean

from bleak import BleakScanner
from bla_payload import BLA_Payload

TARGET_NAME = "kikicker"
TARGET_COMPANY_ID = 0x1337

# Global flag for output mode
RAW_MODE = False


def _format_payload(advertisement_data) -> str:
    """Decode kikicker payload based on mode (human-readable or raw bytes)."""
    manufacturer_data = advertisement_data.manufacturer_data or {}
    
    # Look for our company ID
    if TARGET_COMPANY_ID in manufacturer_data:
        payload_bytes = bytes(manufacturer_data[TARGET_COMPANY_ID])
        if payload_bytes:
            if RAW_MODE:
                # Raw bytes mode
                return f"{TARGET_COMPANY_ID:04x}:{payload_bytes.hex()}"
            else:
                # Human-readable mode
                return BLA_Payload.decode_payload(payload_bytes)
    
    # Fallback for other/unknown manufacturer data
    if manufacturer_data:
        segments = []
        for company_id, payload in sorted(manufacturer_data.items()):
            payload_bytes = bytes(payload)
            hex_payload = payload_bytes.hex() if payload_bytes else "none"
            segments.append(f"{company_id:04x}:{hex_payload}")
        return " ".join(segments)

    return "none"


def _extract_packet_index(advertisement_data) -> int | None:
    manufacturer_data = advertisement_data.manufacturer_data or {}
    if not manufacturer_data:
        return None

    for company_id, payload in sorted(manufacturer_data.items()):
        payload_bytes = bytes(payload)
        if payload_bytes:
            value = int.from_bytes(payload_bytes, "little")
            if value:
                return value
        # Fall back to the manufacturer key when payload bytes are empty/zero.
        return company_id
    return None


async def main():
    deltas: list[float] = []
    last_event_time: float | None = None
    last_payload_text: str | None = None
    unique_payloads: set[str] = set()
    packet_indices_seen: set[int] = set()
    min_index: int | None = None
    max_index: int | None = None

    def detection_callback(device, advertisement_data):
        nonlocal last_event_time, last_payload_text, min_index, max_index

        name = (advertisement_data.local_name or "").lower()
        if TARGET_NAME not in name:
            return

        payload_text = _format_payload(advertisement_data)
        if payload_text == last_payload_text:
            return

        unique_payloads.add(payload_text)

        index_val = _extract_packet_index(advertisement_data)

        now = time.time()
        delta = None if last_event_time is None else now - last_event_time
        last_event_time = now
        if delta is not None:
            deltas.append(delta)

        last_payload_text = payload_text

        if index_val is not None:
            packet_indices_seen.add(index_val)
            if min_index is None or index_val < min_index:
                min_index = index_val
            if max_index is None or index_val > max_index:
                max_index = index_val

        delta_text = "--" if delta is None else f"{delta * 1000:.2f}ms"
        print(f"{payload_text} | delta: {delta_text}")

    try:
        scanner = BleakScanner(detection_callback, scanning_mode="active")
    except TypeError:
        scanner = BleakScanner(scanning_mode="active")
        if hasattr(scanner, "register_detection_callback"):
            scanner.register_detection_callback(detection_callback)

    stop_event = asyncio.Event()

    def handle_sigint(signum, frame): 
        stop_event.set()

    signal.signal(signal.SIGINT, handle_sigint)

    await scanner.start()
    print("Scanning for 'kikicker' advertisements. Press Ctrl+C to stop.")

    try:
        while not stop_event.is_set():
            await asyncio.sleep(0.2)
    finally:
        await scanner.stop()

    if deltas:
        deltas_ms = [value * 1000 for value in deltas]
        print(
            f"Delta stats (ms) min={min(deltas_ms):.2f} max={max(deltas_ms):.2f} "
            f"avg={mean(deltas_ms):.2f}"
        )
    else:
        print("No repeated 'kikicker' advertisements were captured. Stats unavailable.")

    packets_received = len(unique_payloads)
    if packet_indices_seen:
        if min_index is not None and max_index is not None:
            total_packets = max_index - min_index + 1
        else:
            total_packets = packets_received
    else:
        total_packets = packets_received
    print(f"Loss (Received/Total): {packets_received}/{total_packets}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scan for kikicker BLE advertisements')
    parser.add_argument('--raw', action='store_true', 
                        help='Show raw payload bytes instead of decoded format')
    args = parser.parse_args()
    
    RAW_MODE = args.raw
    
    mode_text = "raw bytes" if RAW_MODE else "human-readable"
    print(f"Starting scanner in {mode_text} mode...")
    
    asyncio.run(main())
