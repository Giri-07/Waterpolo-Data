"""
Penalty packet decoder for 0x1D packets.
Handles penalty information for both home and guest teams.
"""

import logging
from .packet_decoder import is_complement_pair, normalize_value


class PenaltyPacketDecoder:
    """
    Decoder for 0x1D penalty packets.
    
    Packet layout (18 complement-value pairs):
      0x1D,
        [C_pen1_mm, PenaltyTimeHome1.mm],      # B1: Penalty 1 Home minutes
        [C_pen1_ss, PenaltyTimeHome1.ss],      # B2: Penalty 1 Home seconds
        [C_player1, PlayerPenHome1],           # B3: Home player number for Penalty 1
        [C_pen2_mm, PenaltyTimeHome2.mm],      # B4: Penalty 2 Home minutes
        [C_pen2_ss, PenaltyTimeHome2.ss],      # B5: Penalty 2 Home seconds
        [C_player2, PlayerPenHome2],           # B6: Home player number for Penalty 2
        [C_misc_mm, MisconductPenaltyTimeHome.mm],  # B7: Misconduct Home minutes
        [C_misc_ss, MisconductPenaltyTimeHome.ss],  # B8: Misconduct Home seconds
        [C_misc_pl, PlayerMiscPenHome],        # B9: Home player for misconduct
        [C_gpen1_mm, PenaltyTimeGuest1.mm],    # B10: Penalty 1 Guest minutes
        [C_gpen1_ss, PenaltyTimeGuest1.ss],    # B11: Penalty 1 Guest seconds
        [C_gplayer1, PlayerPenGuest1],         # B12: Guest player number for Penalty 1
        [C_gpen2_mm, PenaltyTimeGuest2.mm],    # B13: Penalty 2 Guest minutes
        [C_gpen2_ss, PenaltyTimeGuest2.ss],    # B14: Penalty 2 Guest seconds
        [C_gplayer2, PlayerPenGuest2],         # B15: Guest player number for Penalty 2
        [C_gmisc_mm, MisconductPenaltyTimeGuest.mm],  # B16: Misconduct Guest minutes
        [C_gmisc_ss, MisconductPenaltyTimeGuest.ss],  # B17: Misconduct Guest seconds
        [C_gmisc_pl, PlayerMiscPenGuest]       # B18: Guest player for misconduct
    """
    
    PENALTY_PACKET = 0x1D
    
    def __init__(self):
        self.last_logged_penalties = None
        self.pps_count = 0
    
    def decode_penalty_packet(self, buf: bytearray, idx: int, scoreboard: dict, state_lock) -> bool:
        """
        Decode a 0x1D penalty packet starting at buf[idx].
        
        Args:
            buf: Buffer containing packet data
            idx: Starting index of the packet
            scoreboard: Shared scoreboard state dictionary
            state_lock: Threading lock for scoreboard access
        
        Returns:
            True if successfully decoded, False otherwise
        """
        # Need 37 bytes total: 1 (0x1D) + 18 pairs (36 bytes)
        if idx + 37 > len(buf):
            return False
        
        # Extract all 18 complement-value pairs
        pairs = []
        for i in range(18):
            c_byte = buf[idx + 1 + i * 2]
            v_byte = buf[idx + 2 + i * 2]
            if not is_complement_pair(c_byte, v_byte):
                return False
            pairs.append(v_byte)
        
        # Parse penalty data
        # Home penalties
        home_pen1_mm = normalize_value(pairs[0])
        home_pen1_ss = normalize_value(pairs[1])
        home_player1 = normalize_value(pairs[2])
        home_pen2_mm = normalize_value(pairs[3])
        home_pen2_ss = normalize_value(pairs[4])
        home_player2 = normalize_value(pairs[5])
        home_misc_mm = normalize_value(pairs[6])
        home_misc_ss = normalize_value(pairs[7])
        home_misc_player = normalize_value(pairs[8])
        
        # Guest penalties
        guest_pen1_mm = normalize_value(pairs[9])
        guest_pen1_ss = normalize_value(pairs[10])
        guest_player1 = normalize_value(pairs[11])
        guest_pen2_mm = normalize_value(pairs[12])
        guest_pen2_ss = normalize_value(pairs[13])
        guest_player2 = normalize_value(pairs[14])
        guest_misc_mm = normalize_value(pairs[15])
        guest_misc_ss = normalize_value(pairs[16])
        guest_misc_player = normalize_value(pairs[17])
        
        # Ignore penalties with 255 values (invalid/empty state)
        # Set them to 0 to indicate no penalty
        if home_pen1_mm == 255 or home_pen1_ss == 255 or home_player1 == 255:
            home_pen1_mm = home_pen1_ss = home_player1 = 0
        if home_pen2_mm == 255 or home_pen2_ss == 255 or home_player2 == 255:
            home_pen2_mm = home_pen2_ss = home_player2 = 0
        if guest_pen1_mm == 255 or guest_pen1_ss == 255 or guest_player1 == 255:
            guest_pen1_mm = guest_pen1_ss = guest_player1 = 0
        if guest_pen2_mm == 255 or guest_pen2_ss == 255 or guest_player2 == 255:
            guest_pen2_mm = guest_pen2_ss = guest_player2 = 0
        
        # Update scoreboard
        with state_lock:
            # Track which players had penalties before this update
            prev_home_pen = {p.get("player") for p in scoreboard["penalties"]["home"] 
                             if p.get("player") and (p.get("minutes", 0) > 0 or p.get("seconds", 0) > 0)}
            prev_guest_pen = {p.get("player") for p in scoreboard["penalties"]["guest"] 
                              if p.get("player") and (p.get("minutes", 0) > 0 or p.get("seconds", 0) > 0)}
            
            # Home Penalty 1
            scoreboard["penalties"]["home"][0] = {
                "player": home_player1 if home_player1 > 0 else None,
                "minutes": home_pen1_mm,
                "seconds": home_pen1_ss,
                "type": "regular"
            }
            # Home Penalty 2
            scoreboard["penalties"]["home"][1] = {
                "player": home_player2 if home_player2 > 0 else None,
                "minutes": home_pen2_mm,
                "seconds": home_pen2_ss,
                "type": "regular"
            }
            
            # Guest Penalty 1
            scoreboard["penalties"]["guest"][0] = {
                "player": guest_player1 if guest_player1 > 0 else None,
                "minutes": guest_pen1_mm,
                "seconds": guest_pen1_ss,
                "type": "regular"
            }
            # Guest Penalty 2
            scoreboard["penalties"]["guest"][1] = {
                "player": guest_player2 if guest_player2 > 0 else None,
                "minutes": guest_pen2_mm,
                "seconds": guest_pen2_ss,
                "type": "regular"
            }
            
            # Detect NEW penalties (player wasn't penalized before, now is)
            curr_home_pen = {p.get("player") for p in scoreboard["penalties"]["home"] 
                             if p.get("player") and (p.get("minutes", 0) > 0 or p.get("seconds", 0) > 0)}
            curr_guest_pen = {p.get("player") for p in scoreboard["penalties"]["guest"] 
                              if p.get("player") and (p.get("minutes", 0) > 0 or p.get("seconds", 0) > 0)}
            
            new_home_pen = curr_home_pen - prev_home_pen
            new_guest_pen = curr_guest_pen - prev_guest_pen
            
            # Increment cumulative penalty count for newly penalized players
            for player_num in new_home_pen:
                if player_num:
                    count = scoreboard["penalty_counts_home"].get(player_num, 0)
                    scoreboard["penalty_counts_home"][player_num] = min(count + 1, 3)
            
            for player_num in new_guest_pen:
                if player_num:
                    count = scoreboard["penalty_counts_guest"].get(player_num, 0)
                    scoreboard["penalty_counts_guest"][player_num] = min(count + 1, 3)
            
            # Create summary for logging
            penalty_summary = {
                "home": [(home_player1, home_pen1_mm, home_pen1_ss), 
                         (home_player2, home_pen2_mm, home_pen2_ss)],
                "guest": [(guest_player1, guest_pen1_mm, guest_pen1_ss), 
                          (guest_player2, guest_pen2_mm, guest_pen2_ss)]
            }
            
            # Log only if changed
            if penalty_summary != self.last_logged_penalties:
                active_penalties = []
                for team, team_name in [("home", "Home"), ("guest", "Guest")]:
                    for i, (player, mm, ss) in enumerate(penalty_summary[team], 1):
                        if player > 0 and (mm > 0 or ss > 0):
                            active_penalties.append(f"{team_name} P{i}: #{player} {mm:02d}:{ss:02d}")
                
                if active_penalties:
                    logging.info("[Penalties] %s", " | ".join(active_penalties))
                self.last_logged_penalties = penalty_summary
        
        self.pps_count += 1
        return True
