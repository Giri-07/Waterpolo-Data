"""
Time packet decoder for 0x16 packets.
Handles main clock time, action time, timeout information, scores, and period data.
"""

import time
import logging
from .packet_decoder import is_complement_pair, popcount4


class TimePacketDecoder:
    """
    Decoder for 0x16 time packets.
    
    Packet layout:
      0x16,
        [Cmm, MM],       # pair1  -> minutes
        [Css, SS],       # pair2  -> seconds
        [Cact, ACT],     # pair3  -> action time
        [Cfl, FLAGS],    # pair4  -> flags
        [Cb5, B5],       # pair5  -> Timeout seconds in lower 7 bits; MSB=ActionON
        [Chs, HOME],     # pair6  -> home score (optional)
        [Cgs, GUEST],    # pair7  -> guest score (optional)
        [Cpr, PERIOD],   # pair8  -> period (optional)
        [Cb9, B9],       # pair9  -> timeouts used (optional)
    """
    
    TIME_PACKET = 0x16
    
    def __init__(self):
        self.last_logged_clock = None
        self.pps_count = 0
        self.pps_window_start = time.time()
        self.last_b9_logged = (-1, -1)
        self.last_action_time = None  # Track previous action time
        self.last_timeout_secs = 0     # Track previous timeout seconds
        
    def decode_time_packet(self, buf: bytearray, idx: int, scoreboard: dict, state_lock) -> tuple:
        """
        Decode a 0x16 time packet starting at buf[idx].
        
        Args:
            buf: Buffer containing packet data
            idx: Starting index of the packet
            scoreboard: Shared scoreboard state dictionary
            state_lock: Threading lock for scoreboard access
        
        Returns:
            Tuple of (success, main_time_str, action_display, playing) or (False, None, None, None)
        """
        # Need at least 9 bytes for basic packet (1 + 4 pairs = 9 bytes)
        if idx + 9 > len(buf):
            return (False, None, None, None)
        
        c_mm, mm = buf[idx+1], buf[idx+2]
        c_ss, ss = buf[idx+3], buf[idx+4]
        c_flags, flags = buf[idx+5], buf[idx+6]
        c_act, act = buf[idx+7], buf[idx+8]
        
        if not (is_complement_pair(c_mm, mm) and
                is_complement_pair(c_ss, ss) and
                is_complement_pair(c_flags, flags) and
                is_complement_pair(c_act, act)):
            return (False, None, None, None)
        
        # Validate time ranges: 0-8 minutes, 0-59 seconds
        if mm > 8 or ss > 59:
            return (False, None, None, None)
        
        main_str = f"{mm:02d}:{ss:02d}"
        
        # PAIR 5 (Timeout secs in lower 7 bits)
        timeout_secs = 0
        if idx + 11 <= len(buf):
            c_b5, b5 = buf[idx+9], buf[idx+10]
            if is_complement_pair(c_b5, b5):
                timeout_secs = b5 & 0x7F  # 0–127
        
        # ACTION / TIMEOUT DISPLAY RULE
        if 1 <= timeout_secs <= 60:
            # Timeout is active (B5 > 0), display timeout seconds
            action_display = f"{timeout_secs:02d}"
        else:
            # No timeout active, display action clock
            if act == 0xAA:
                # 0xAA is "no data" sentinel, display as 00
                action_display = "00"
            elif 1 <= act <= 30:
                # Valid action clock range: 1-30 seconds
                action_display = f"{act:02d}"
            elif act == 0:
                # Action clock at 0 - validate this is legitimate
                # Suspicious if: previous action time was > 0 AND no timeout was active
                if (self.last_action_time is not None and 
                    self.last_action_time > 0 and 
                    self.last_timeout_secs == 0 and 
                    timeout_secs == 0):
                    # Action time suddenly went to 0 without timeout - may be bad data
                    logging.warning(f"[0x16] Suspicious: Action time dropped from {self.last_action_time} to 0 without timeout")
                    # Still accept it but log the warning
                else:
                    logging.debug(f"[0x16] Action time is 0 (timeout ended or game paused)")
                action_display = "00"
            elif 31 <= act <= 60:
                # Extended range for special cases (some systems may use this)
                logging.debug(f"[0x16] Action time {act} in extended range (31-60)")
                action_display = f"{act:02d}"
            else:
                # Invalid action time value
                logging.warning(f"[0x16] Invalid action time: {act}, rejecting packet")
                return (False, None, None, None)
        
        # Update tracking for next packet
        self.last_action_time = act if timeout_secs == 0 else None
        self.last_timeout_secs = timeout_secs
        
        playing = bool(flags & 0b00010000)
        
        # Decode score + period (optional)
        if idx + 17 <= len(buf):
            c_skip, skip = buf[idx+9], buf[idx+10]
            c_home, home = buf[idx+11], buf[idx+12]
            c_guest, guest = buf[idx+13], buf[idx+14]
            c_per, per = buf[idx+15], buf[idx+16]
            
            if (is_complement_pair(c_home, home) and
                is_complement_pair(c_guest, guest) and
                is_complement_pair(c_per, per)):
                with state_lock:
                    # Validate and update scores (reasonable range 0-50)
                    if home != 0xAA and 0 <= home <= 50:
                        scoreboard["home_score"] = home
                    elif home != 0xAA:
                        logging.warning(f"[0x16] Invalid home score: {home}, ignoring")
                    
                    if guest != 0xAA and 0 <= guest <= 50:
                        scoreboard["guest_score"] = guest
                    elif guest != 0xAA:
                        logging.warning(f"[0x16] Invalid guest score: {guest}, ignoring")
                    
                    # Validate and update period (reasonable range 1-4)
                    if per != 0xAA and 1 <= per <= 4:
                        scoreboard["period"] = per
                    elif per != 0xAA:
                        logging.warning(f"[0x16] Invalid period: {per}, ignoring")
        
        # Decode B9 (timeouts used) - optional pair9
        if idx + 19 <= len(buf):
            c_b9, b9 = buf[idx+17], buf[idx+18]
            
            if is_complement_pair(c_b9, b9):
                # B9 contains timeout information
                # Higher 4 bits: Home timeouts used (direct value, not bit count)
                # Lower 4 bits: Guest timeouts used (direct value, not bit count)
                home_used = (b9 >> 4) & 0x0F
                guest_used = b9 & 0x0F
                
                # Validate timeout counts (reasonable range 0-2)
                if not (0 <= home_used <= 2):
                    logging.warning(f"[B9 in 0x16] Invalid home timeout count: {home_used}, ignoring")
                    home_used = scoreboard.get("timeouts_home", 0)
                
                if not (0 <= guest_used <= 2):
                    logging.warning(f"[B9 in 0x16] Invalid guest timeout count: {guest_used}, ignoring")
                    guest_used = scoreboard.get("timeouts_guest", 0)
                
                with state_lock:
                    changed = (scoreboard["timeouts_home"] != home_used) or \
                              (scoreboard["timeouts_guest"] != guest_used)
                    scoreboard["timeouts_home"] = home_used
                    scoreboard["timeouts_guest"] = guest_used
                
                if changed and self.last_b9_logged != (home_used, guest_used):
                    logging.info(f"[B9 in 0x16] TO Used → Home={home_used}, Guest={guest_used}")
                    self.last_b9_logged = (home_used, guest_used)
        
        # Update state
        with state_lock:
            scoreboard["main_time"] = main_str
            scoreboard["action_time"] = action_display
        
        self.pps_count += 1
        
        if main_str != self.last_logged_clock:
            logging.info("[Clock] %s  Action/TO: %s", main_str, action_display)
            self.last_logged_clock = main_str
        
        return (True, main_str, action_display, playing)


class TimeoutDecoder:
    """
    Decoder for 0xB9 timeout packets.
    Handles both single-pair and two-pair variants.
    """
    
    TIMEOUT_PACKET = 0xB9
    
    def __init__(self):
        self.last_b9_logged = (-1, -1)
    
    def decode_timeout_single_pair(self, buf: bytearray, idx: int, scoreboard: dict, state_lock) -> bool:
        """
        Decode single-pair B9 timeout packet: B9, Cval, VAL
        
        Returns:
            True if successfully decoded, False otherwise
        """
        if idx + 3 > len(buf):
            return False
        
        if not is_complement_pair(buf[idx+1], buf[idx+2]):
            return False
        
        val = buf[idx+2] & 0xFF
        guest_used = popcount4((val >> 4) & 0x0F)
        home_used = popcount4(val & 0x0F)
        
        with state_lock:
            changed = (scoreboard["timeouts_home"] != home_used) or \
                      (scoreboard["timeouts_guest"] != guest_used)
            scoreboard["timeouts_home"] = home_used
            scoreboard["timeouts_guest"] = guest_used
        
        if changed and self.last_b9_logged != (home_used, guest_used):
            logging.info(f"[B9] TO Used changed → Home={home_used}, Guest={guest_used}")
            self.last_b9_logged = (home_used, guest_used)
        
        return True
    
    def decode_timeout_two_pair(self, buf: bytearray, idx: int, scoreboard: dict, state_lock) -> bool:
        """
        Decode two-pair B9 timeout packet: B9, Cg, GTO, Ch, HTO
        
        Returns:
            True if successfully decoded, False otherwise
        """
        if idx + 5 > len(buf):
            return False
        
        cg, gto = buf[idx+1], buf[idx+2]
        ch, hto = buf[idx+3], buf[idx+4]
        
        if not (is_complement_pair(cg, gto) and is_complement_pair(ch, hto)):
            return False
        
        guest_used = popcount4(gto & 0x0F)
        home_used = popcount4(hto & 0x0F)
        
        with state_lock:
            changed = (scoreboard["timeouts_home"] != home_used) or \
                      (scoreboard["timeouts_guest"] != guest_used)
            scoreboard["timeouts_home"] = home_used
            scoreboard["timeouts_guest"] = guest_used
        
        if changed and self.last_b9_logged != (home_used, guest_used):
            logging.info(f"[B9] TO Used changed → Home={home_used}, Guest={guest_used}")
            self.last_b9_logged = (home_used, guest_used)
        
        return True
