"""
Player points packet decoders for 0x19 and 0x1A packets.
Handles player points data for both home and guest teams.
"""

from .packet_decoder import is_complement_pair


class PlayerPointsDecoder:
    """
    Decoder for 0x19 (home) and 0x1A (guest) player points packets.
    
    Packet layout for both types:
      0x19 or 0x1A,
        [C_p1, player1_points],    # Player 1 points
        [C_p2, player2_points],    # Player 2 points
        ...
        [C_p14, player14_points]   # Player 14 points
    
    Total: 1 byte (packet type) + 14 pairs (28 bytes) = 29 bytes
    """
    
    HOME_POINTS_PACKET = 0x19
    GUEST_POINTS_PACKET = 0x1A
    
    def decode_home_player_points(self, buf: bytearray, idx: int, scoreboard: dict, state_lock) -> bool:
        """
        Decode a 0x19 home player points packet starting at buf[idx].
        Updates scoreboard['players_home'][i]['points'] for i in range(14).
        
        Args:
            buf: Buffer containing packet data
            idx: Starting index of the packet
            scoreboard: Shared scoreboard state dictionary
            state_lock: Threading lock for scoreboard access
        
        Returns:
            True if successfully decoded, False otherwise
        """
        # Need 29 bytes: 1 (0x19) + 14 pairs (28 bytes)
        if idx + 29 > len(buf):
            return False
        
        pairs = []
        for i in range(14):
            c_byte = buf[idx + 1 + i * 2]
            v_byte = buf[idx + 2 + i * 2]
            if not is_complement_pair(c_byte, v_byte):
                return False
            pairs.append(v_byte)
        
        with state_lock:
            for i in range(14):
                scoreboard['players_home'][i]['points'] = pairs[i]
        
        return True
    
    def decode_guest_player_points(self, buf: bytearray, idx: int, scoreboard: dict, state_lock) -> bool:
        """
        Decode a 0x1A guest player points packet starting at buf[idx].
        Updates scoreboard['players_guest'][i]['points'] for i in range(14).
        
        Args:
            buf: Buffer containing packet data
            idx: Starting index of the packet
            scoreboard: Shared scoreboard state dictionary
            state_lock: Threading lock for scoreboard access
        
        Returns:
            True if successfully decoded, False otherwise
        """
        # Need 29 bytes: 1 (0x1A) + 14 pairs (28 bytes)
        if idx + 29 > len(buf):
            return False
        
        pairs = []
        for i in range(14):
            c_byte = buf[idx + 1 + i * 2]
            v_byte = buf[idx + 2 + i * 2]
            if not is_complement_pair(c_byte, v_byte):
                return False
            pairs.append(v_byte)
        
        with state_lock:
            for i in range(14):
                scoreboard['players_guest'][i]['points'] = pairs[i]
        
        return True
