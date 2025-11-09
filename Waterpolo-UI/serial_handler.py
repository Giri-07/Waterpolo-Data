"""
Serial communication handler for Waterpolo Scoreboard.
Handles reading from serial port and decoding packets.
"""

import time
import logging
import threading

try:
    import serial  # type: ignore
except Exception:
    serial = None

from config import (
    PORT, BAUD, TIME_PACKET, PENALTY_PACKET,
    PLAYER_POINTS_PACKET, GUEST_POINTS_PACKET,
    FOULS_PACKET, NO_DATA_LOG_INTERVAL, PPS_REPORT_INTERVAL
)
from state import scoreboard, state_lock, update_last_valid_packet_time
from decoders import (
    TimePacketDecoder,
    TimeoutDecoder,
    PenaltyPacketDecoder,
    PlayerPointsDecoder,
    FoulsDecoder
)


# Initialize decoder instances
_time_decoder = TimePacketDecoder()
_timeout_decoder = TimeoutDecoder()
_penalty_decoder = PenaltyPacketDecoder()
_player_decoder = PlayerPointsDecoder()
_fouls_decoder = FoulsDecoder()

# PPS tracking
_pps_window_start = time.time()


def _pps_maybe_report():
    """Report packets per second statistics."""
    global _pps_window_start
    now = time.time()
    if now - _pps_window_start >= PPS_REPORT_INTERVAL:
        pps_16 = _time_decoder.pps_count / max(now - _pps_window_start, 1e-6)
        pps_1d = _penalty_decoder.pps_count / max(now - _pps_window_start, 1e-6)
        logging.info("Packets/sec: 0x16=%.2f, 0x1D=%.2f", pps_16, pps_1d)
        _pps_window_start = now
        _time_decoder.pps_count = 0
        _penalty_decoder.pps_count = 0


def decode_stream_chunks(ser, on_time_update):
    """
    Read serial stream in chunks, scan for TIME_PACKET (0x16), PENALTY_PACKET (0x1D), and B9,
    validate complement pairs, and call on_time_update(main_time_str, action_display, playing).
    Updates scoreboard state with time, scores, penalties, and timeout information.
    """
    buf = bytearray()
    next_no_data_log = time.time() + NO_DATA_LOG_INTERVAL

    while True:
        try:
            chunk = ser.read(128)
        except Exception as e:
            logging.exception("Serial read error: %s", e)
            time.sleep(0.2)
            continue

        if not chunk:
            now = time.time()
            if now >= next_no_data_log:
                logging.info("No data received on %s...", PORT)
                next_no_data_log = now + NO_DATA_LOG_INTERVAL
            time.sleep(0.01)
            # Even if no new data, continue scanning for any residual B9/16 in buf
        else:
            buf += chunk
            if len(buf) > 4096:
                buf = buf[-2048:]

        i = 0
        while True:
            # ---------- FOULS PACKET (0x02) ----------
            idx_02 = buf.find(bytes([FOULS_PACKET]), i)
            if idx_02 >= 0 and idx_02 < len(buf):
                if _fouls_decoder.decode_fouls(buf, idx_02, scoreboard, state_lock):
                    # Successfully decoded, remove from buffer
                    del buf[:idx_02 + 29]
                    i = 0
                    continue
                else:
                    i = idx_02 + 1
                    # Don't continue here, also check for other packets

            # ---------- PLAYER POINTS PACKET (0x19) ----------
            idx_19 = buf.find(bytes([PLAYER_POINTS_PACKET]), i)
            if idx_19 >= 0 and idx_19 < len(buf):
                if _player_decoder.decode_home_player_points(buf, idx_19, scoreboard, state_lock):
                    # Successfully decoded, remove from buffer
                    del buf[:idx_19 + 29]
                    i = 0
                    continue
                else:
                    i = idx_19 + 1
                    # Don't continue here, also check for other packets

            # ---------- GUEST PLAYER POINTS PACKET (0x1A) ----------
            idx_1a = buf.find(bytes([GUEST_POINTS_PACKET]), i)
            if idx_1a >= 0 and idx_1a < len(buf):
                if _player_decoder.decode_guest_player_points(buf, idx_1a, scoreboard, state_lock):
                    # Successfully decoded, remove from buffer
                    del buf[:idx_1a + 29]
                    i = 0
                    continue
                else:
                    i = idx_1a + 1
                    # Don't continue here, also check for other packets

            # ---------- PENALTY PACKET (0x1D) ----------
            idx_1d = buf.find(bytes([PENALTY_PACKET]), i)
            if idx_1d >= 0 and idx_1d < len(buf):
                if _penalty_decoder.decode_penalty_packet(buf, idx_1d, scoreboard, state_lock):
                    # Successfully decoded, remove from buffer
                    del buf[:idx_1d + 37]
                    i = 0
                    continue
                else:
                    # Not enough bytes yet or invalid, try next position
                    i = idx_1d + 1
                    # Don't continue here, also check for 0x16

            # ---------- TIME PACKET (0x16) ----------
            idx = buf.find(bytes([TIME_PACKET]), i)
            if idx < 0:
                # No 0x16 ahead — try to handle any B9/1D that might be present, then break
                # (B9 handler below also runs when 0x16 was found; here is a final pass)

                # Check for any remaining 0x1D packets
                idx_1d_final = buf.find(bytes([PENALTY_PACKET]))
                if idx_1d_final >= 0:
                    if _penalty_decoder.decode_penalty_packet(buf, idx_1d_final, scoreboard, state_lock):
                        del buf[:idx_1d_final + 37]
                        continue
                
                # ------------------ B9: Timeouts Used ------------------
                idx_b9 = buf.find(bytes([0xB9]))
                if idx_b9 >= 0:
                    # Try single-pair form first
                    if _timeout_decoder.decode_timeout_single_pair(buf, idx_b9, scoreboard, state_lock):
                        del buf[:idx_b9+3]
                        continue
                    
                    # Try two-pair form
                    if _timeout_decoder.decode_timeout_two_pair(buf, idx_b9, scoreboard, state_lock):
                        del buf[:idx_b9+5]
                        continue

                break  # nothing more we can parse right now

            # Decode time packet using decoder
            success, main_str, action_display, playing = _time_decoder.decode_time_packet(
                buf, idx, scoreboard, state_lock
            )
            
            if success:
                if main_str and action_display is not None:
                    on_time_update(main_str, action_display, playing)
                
                update_last_valid_packet_time()
                _pps_maybe_report()

                # Consume this 0x16 frame
                del buf[:idx+9]
                i = 0

                # ------------------ Also parse any B9 that might now be complete ------------------
                while True:
                    idx_b9 = buf.find(bytes([0xB9]))
                    if idx_b9 < 0:
                        break

                    # Try single-pair form first
                    if _timeout_decoder.decode_timeout_single_pair(buf, idx_b9, scoreboard, state_lock):
                        del buf[:idx_b9+3]
                        i = 0
                        continue
                    
                    # Try two-pair form
                    if _timeout_decoder.decode_timeout_two_pair(buf, idx_b9, scoreboard, state_lock):
                        del buf[:idx_b9+5]
                        i = 0
                        continue

                    # Not enough bytes for B9 yet
                    break

            else:
                i = idx + 1


def serial_reader_thread(on_time_update):
    """Thread function to read from serial port and decode packets."""
    if serial is None:
        logging.error("pyserial not installed. Install with: pip install pyserial")
        return
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.2)
        logging.info("Opened serial port %s @ %d", PORT, BAUD)
    except Exception as e:
        logging.error("Failed to open serial: %s", e)
        return

    decode_stream_chunks(ser, on_time_update)


def start_serial_reader(on_time_update_callback):
    """Start the serial reader thread."""
    t_reader = threading.Thread(
        target=serial_reader_thread,
        args=(on_time_update_callback,),
        daemon=True,
        name="SerialReader",
    )
    t_reader.start()
    return t_reader
