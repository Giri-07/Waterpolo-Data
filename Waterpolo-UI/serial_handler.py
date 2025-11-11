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
            # Find all packet types starting from position i
            idx_02 = buf.find(bytes([FOULS_PACKET]), i)
            idx_19 = buf.find(bytes([PLAYER_POINTS_PACKET]), i)
            idx_1a = buf.find(bytes([GUEST_POINTS_PACKET]), i)
            idx_1d = buf.find(bytes([PENALTY_PACKET]), i)
            idx_16 = buf.find(bytes([TIME_PACKET]), i)
            
            # Find the earliest packet in the buffer
            candidates = []
            if idx_02 >= 0:
                candidates.append((idx_02, '0x02'))
            if idx_19 >= 0:
                candidates.append((idx_19, '0x19'))
            if idx_1a >= 0:
                candidates.append((idx_1a, '0x1A'))
            if idx_1d >= 0:
                candidates.append((idx_1d, '0x1D'))
            if idx_16 >= 0:
                candidates.append((idx_16, '0x16'))
            
            if not candidates:
                # No packets found, try final cleanup
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
            
            # Process the earliest packet
            earliest_idx, packet_type = min(candidates)
            
            # ---------- FOULS PACKET (0x02) ----------
            if packet_type == '0x02':
                logging.debug(f"[0x02] Found at buffer position {earliest_idx}, buffer size={len(buf)}")
                # Quick validation: check if we have enough bytes and first complement pair looks valid
                if earliest_idx + 29 <= len(buf):
                    # Check first complement pair as a quick sanity check
                    first_c = buf[earliest_idx + 1]
                    first_v = buf[earliest_idx + 2]
                    quick_check = ((~first_v) & 0xFF) == (first_c & 0xFF)
                    
                    if quick_check:
                        if _fouls_decoder.decode_fouls(buf, earliest_idx, scoreboard, state_lock):
                            logging.info("[0x02] Successfully decoded fouls packet")
                            update_last_valid_packet_time()
                            # Successfully decoded, remove from buffer
                            del buf[:earliest_idx + 29]
                            i = 0
                            continue
                        else:
                            logging.debug(f"[0x02] Failed to decode at pos {earliest_idx} - validation failed")
                            i = earliest_idx + 1
                            continue
                    else:
                        logging.debug(f"[0x02] Quick check failed at pos {earliest_idx} (first pair invalid), skipping")
                        i = earliest_idx + 1
                        continue
                else:
                    logging.debug(f"[0x02] Insufficient data at pos {earliest_idx}, need more bytes")
                    # If we're at the end of buffer, break and wait for more data
                    if earliest_idx == len(buf) - 1 or len(buf) - earliest_idx < 29:
                        break
                    i = earliest_idx + 1
                    continue

            # ---------- PLAYER POINTS PACKET (0x19) ----------
            elif packet_type == '0x19':
                if _player_decoder.decode_home_player_points(buf, earliest_idx, scoreboard, state_lock):
                    # Successfully decoded, remove from buffer
                    del buf[:earliest_idx + 29]
                    i = 0
                    continue
                else:
                    i = earliest_idx + 1
                    continue

            # ---------- GUEST PLAYER POINTS PACKET (0x1A) ----------
            elif packet_type == '0x1A':
                if _player_decoder.decode_guest_player_points(buf, earliest_idx, scoreboard, state_lock):
                    # Successfully decoded, remove from buffer
                    del buf[:earliest_idx + 29]
                    i = 0
                    continue
                else:
                    i = earliest_idx + 1
                    continue

            # ---------- PENALTY PACKET (0x1D) ----------
            elif packet_type == '0x1D':
                if _penalty_decoder.decode_penalty_packet(buf, earliest_idx, scoreboard, state_lock):
                    # Successfully decoded, remove from buffer
                    del buf[:earliest_idx + 37]
                    i = 0
                    continue
                else:
                    # Not enough bytes yet or invalid, try next position
                    i = earliest_idx + 1
                    continue

            # ---------- TIME PACKET (0x16) ----------
            elif packet_type == '0x16':
                idx = earliest_idx
                
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
                    continue

                else:
                    i = idx + 1
                    continue


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
