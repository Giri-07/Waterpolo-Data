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
        # Need 29 bytes: 1 (0x02) + 14 pairs (28 bytes)
        if idx + 29 > len(buf):
            return False
        
        pairs = []
        for i in range(14):
            c_byte = buf[idx + 1 + i * 2]
            v_byte = buf[idx + 2 + i * 2]
            if not is_complement_pair(c_byte, v_byte):
                return False
            pairs.append(v_byte)
        
        # Extract home and guest fouls from each byte
        with state_lock:
            for i in range(14):
                fouls_byte = pairs[i]
                home_fouls = (fouls_byte >> 4) & 0x0F  # Higher 4 bits
                guest_fouls = fouls_byte & 0x0F         # Lower 4 bits
                
                scoreboard['players_home'][i]['fouls'] = home_fouls
                scoreboard['players_guest'][i]['fouls'] = guest_fouls
        
        return True
