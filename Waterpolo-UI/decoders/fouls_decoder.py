"""
Personal fouls packet decoder for 0x02 packet.
Handles player personal fouls data for both home and guest teams.
"""

from .packet_decoder import is_complement_pair


class FoulsDecoder:
    """
    Decoder for 0x02 personal fouls packet.
    
    Packet layout:
      0x02,
        [C_f1, fouls_byte1],    # Player 1 (home) & Player 1 (guest) fouls
        [C_f2, fouls_byte2],    # Player 2 (home) & Player 2 (guest) fouls
        ...
        [C_f14, fouls_byte14]   # Player 14 (home) & Player 14 (guest) fouls
    
    Each fouls byte contains:
      - Higher 4 bits: Home player fouls (0-15)
      - Lower 4 bits: Guest player fouls (0-15)
    
    Total: 1 byte (packet type) + 14 pairs (28 bytes) = 29 bytes
    """
    
    FOULS_PACKET = 0x02
    
    def decode_fouls(self, buf: bytearray, idx: int, scoreboard: dict, state_lock) -> bool:
        """
        Decode a 0x02 personal fouls packet starting at buf[idx].
        Updates scoreboard['players_home'][i]['fouls'] and 
        scoreboard['players_guest'][i]['fouls'] for i in range(14).
        
        Args:
            buf: Buffer containing packet data
            idx: Starting index of the packet
            scoreboard: Shared scoreboard state dictionary
            state_lock: Threading lock for scoreboard access
        
        Returns:
            True if successfully decoded, False otherwise
        """
        import logging
        
        # Need 29 bytes: 1 (0x02) + 14 pairs (28 bytes)
        if idx + 29 > len(buf):
            logging.debug(f"[0x02] Insufficient buffer: need 29 bytes, have {len(buf) - idx}")
            return False
        
        # Verify first byte is 0x02
        if buf[idx] != 0x02:
            logging.warning(f"[0x02] Invalid packet ID at idx {idx}: 0x{buf[idx]:02x} (expected 0x02)")
            return False
        
        # Log raw packet for debugging
        raw_packet = buf[idx:idx+29]
        logging.debug(f"[0x02] Raw packet (hex): {raw_packet.hex()}")
        
        # Validate all complement pairs first before processing
        pairs = []
        validation_failures = []
        for i in range(14):
            c_byte = buf[idx + 1 + i * 2]
            v_byte = buf[idx + 2 + i * 2]
            if not is_complement_pair(c_byte, v_byte):
                validation_failures.append((i+1, c_byte, v_byte))
                # Only log first failure to reduce noise
                if len(validation_failures) == 1:
                    logging.debug(
                        f"[0x02] Invalid complement pair at player {i+1}: "
                        f"C=0x{c_byte:02x}, V=0x{v_byte:02x}, Expected C=0x{(~v_byte & 0xFF):02x}"
                    )
                # Early exit if multiple failures (likely not a real packet)
                if len(validation_failures) > 3:
                    logging.debug(f"[0x02] Multiple validation failures ({len(validation_failures)}), likely false positive 0x02")
                    return False
            else:
                pairs.append(v_byte)
        
        # If any validation failures occurred, this is not a valid packet
        if validation_failures:
            return False
        
        # Extract home and guest fouls from each byte
        home_fouls_list = []
        guest_fouls_list = []
        
        for i in range(14):
            fouls_byte = pairs[i]
            home_fouls = (fouls_byte >> 4) & 0x0F  # Higher 4 bits
            guest_fouls = fouls_byte & 0x0F         # Lower 4 bits
            home_fouls_list.append(home_fouls)
            guest_fouls_list.append(guest_fouls)
        
        # Detect garbage data patterns
        # Pattern 1: Long sequential runs (5+ consecutive incrementing values)
        # Example: [3,4,5,6,7,8,9,10,11,12,13,14,15]
        def has_long_sequence(values):
            max_sequence = 0
            current_sequence = 1
            for i in range(1, len(values)):
                if values[i] > 0 and values[i] == values[i-1] + 1:
                    current_sequence += 1
                    max_sequence = max(max_sequence, current_sequence)
                else:
                    current_sequence = 1
            return max_sequence >= 5
        
        # Pattern 2: Too many high values (>3 players with >4 fouls is unrealistic)
        high_foul_count = sum(1 for f in home_fouls_list + guest_fouls_list if f > 4)
        
        # Pattern 3: Any single value >5 (extremely rare)
        has_extreme_values = any(f > 5 for f in home_fouls_list + guest_fouls_list)
        
        is_garbage = (
            has_long_sequence(home_fouls_list) or 
            has_long_sequence(guest_fouls_list) or
            high_foul_count > 3 or
            has_extreme_values
        )
        
        if is_garbage:
            logging.error("[0x02] GARBAGE DATA DETECTED!")
            logging.error(f"[0x02] Guest fouls: {guest_fouls_list}")
            logging.error(f"[0x02] Home fouls: {home_fouls_list}")
            logging.error(f"[0x02] Long sequence: Home={has_long_sequence(home_fouls_list)}, Guest={has_long_sequence(guest_fouls_list)}")
            logging.error(f"[0x02] High foul count: {high_foul_count} players with >4 fouls")
            logging.error(f"[0x02] Extreme values: {has_extreme_values}")
            logging.error("[0x02] This is likely NOT a valid 0x02 packet - ignoring!")
            return False
        
        # Update state only if data looks valid
        with state_lock:
            for i in range(14):
                scoreboard['players_home'][i]['fouls'] = home_fouls_list[i]
                scoreboard['players_guest'][i]['fouls'] = guest_fouls_list[i]
        
        # Log non-zero fouls
        has_fouls = False
        for i in range(14):
            if home_fouls_list[i] > 0 or guest_fouls_list[i] > 0:
                if not has_fouls:
                    logging.info("[0x02] Valid fouls detected:")
                    has_fouls = True
                logging.info(f"  Player {i+1}: Home={home_fouls_list[i]}, Guest={guest_fouls_list[i]}")
        
        if not has_fouls:
            logging.debug("[0x02] Packet decoded - all fouls are zero")
        
        return True
