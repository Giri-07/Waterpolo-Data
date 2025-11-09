"""
Unit tests for Waterpolo Scoreboard decoders.
"""

import logging
from config import TIME_PACKET, PENALTY_PACKET, FOULS_PACKET
from state import scoreboard, state_lock
from decoders import (
    TimePacketDecoder,
    PenaltyPacketDecoder,
    PlayerPointsDecoder,
    FoulsDecoder,
    is_complement_pair
)


def setup_logging():
    """Setup basic logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s",
        handlers=[logging.StreamHandler()],
        force=True,
    )
    logging.info("Console logging enabled (minimal)")


def run_tests() -> int:
    """Run all unit tests for packet decoders."""
    setup_logging()
    logging.info("Running tests...")
    
    # Initialize decoders
    _time_decoder = TimePacketDecoder()
    _penalty_decoder = PenaltyPacketDecoder()
    _player_decoder = PlayerPointsDecoder()
    _fouls_decoder = FoulsDecoder()
    
    # Test fouls packet (0x02) decoder
    # Example: Player 1: home 3 fouls, guest 2 fouls
    #          Player 2: home 1 foul, guest 0 fouls
    #          Players 3-14: no fouls
    sample_fouls = bytearray([
        FOULS_PACKET,
        0xCD, 0x32,  # Player 1: home=3 (0x3), guest=2 (0x2) -> 0x32
        0xFE, 0x01,  # Player 2: home=0 (0x0), guest=1 (0x1) -> 0x01
        0xFF, 0x00,  # Player 3: no fouls
        0xFF, 0x00,  # Player 4: no fouls
        0xFF, 0x00,  # Player 5: no fouls
        0xFF, 0x00,  # Player 6: no fouls
        0xFF, 0x00,  # Player 7: no fouls
        0xFF, 0x00,  # Player 8: no fouls
        0xFF, 0x00,  # Player 9: no fouls
        0xFF, 0x00,  # Player 10: no fouls
        0xFF, 0x00,  # Player 11: no fouls
        0xFF, 0x00,  # Player 12: no fouls
        0xFF, 0x00,  # Player 13: no fouls
        0xFF, 0x00   # Player 14: no fouls
    ])
    
    result = _fouls_decoder.decode_fouls(sample_fouls, 0, scoreboard, state_lock)
    assert result == True, "Fouls packet decode failed"
    with state_lock:
        # Check player 1
        assert scoreboard['players_home'][0]['fouls'] == 3, "Player 1 home fouls incorrect"
        assert scoreboard['players_guest'][0]['fouls'] == 2, "Player 1 guest fouls incorrect"
        # Check player 2
        assert scoreboard['players_home'][1]['fouls'] == 0, "Player 2 home fouls incorrect"
        assert scoreboard['players_guest'][1]['fouls'] == 1, "Player 2 guest fouls incorrect"
        # Check remaining players have no fouls
        for i in range(2, 14):
            assert scoreboard['players_home'][i]['fouls'] == 0, f"Player {i+1} home fouls should be 0"
            assert scoreboard['players_guest'][i]['fouls'] == 0, f"Player {i+1} guest fouls should be 0"
    logging.info("Fouls packet test passed ✅ (0x02)")
    
    # Test guest player points packet (0x1A) decoder
    # Example: Guest player points: 11 to 24
    sample_guest_points = bytearray([0x1A] + sum([[~i & 0xFF, i] for i in range(11, 25)], []))
    result = _player_decoder.decode_guest_player_points(sample_guest_points, 0, scoreboard, state_lock)
    assert result == True, "Guest player points packet decode failed"
    with state_lock:
        for i in range(14):
            assert scoreboard['players_guest'][i]['points'] == i + 11, f"Guest Player {i+1} points incorrect"
    logging.info("Guest player points packet test passed ✅ (0x1A)")
    
    # Test player points packet (0x19) decoder
    # Example: Home player points: 1 to 14
    sample_points = bytearray([0x19] + sum([[~i & 0xFF, i] for i in range(1, 15)], []))
    result = _player_decoder.decode_home_player_points(sample_points, 0, scoreboard, state_lock)
    assert result == True, "Player points packet decode failed"
    with state_lock:
        for i in range(14):
            assert scoreboard['players_home'][i]['points'] == i + 1, f"Player {i+1} points incorrect"
    logging.info("Player points packet test passed ✅ (0x19)")

    # Time-only (4 pairs): 16, FF 00, E0 1F, F6 09, CE 31  (order: mm, ss, act, flags)
    def scan_time_only(buf: bytearray):
        results = []
        while True:
            idx = buf.find(bytes([TIME_PACKET]))
            if idx < 0 or idx + 9 > len(buf):
                break
            c_mm, mm = buf[idx + 1], buf[idx + 2]
            c_ss, ss = buf[idx + 3], buf[idx + 4]
            c_ac, ac = buf[idx + 5], buf[idx + 6]
            c_fl, fl = buf[idx + 7], buf[idx + 8]
            if (
                is_complement_pair(c_mm, mm)
                and is_complement_pair(c_ss, ss)
                and is_complement_pair(c_ac, ac)
                and is_complement_pair(c_fl, fl)
            ):
                results.append((f"{mm:02d}:{ss:02d}", f"{ac:02d}"))
            del buf[:idx + 9]
        return results

    sample_time_only = bytearray(
        [TIME_PACKET, 0xFF, 0x00, 0xE0, 0x1F, 0xF6, 0x09, 0xCE, 0x31]
    )
    out = scan_time_only(sample_time_only)
    assert out and out[0] == ("00:31", "09"), "Time-only decode failed"

    # Full frame example (minutes=08, seconds=00, action=09, home=06, guest=03, period=04)
    # 16 F7 08 FF 00 F6 09 ED 12 FF 00 F9 06 FC 03 FB 04
    sample_full = bytearray(
        [
            TIME_PACKET, 0xF7, 0x08, 0xFF, 0x00, 0xF6, 0x09, 0xED, 0x12,
            0xFF, 0x00, 0xF9, 0x06, 0xFC, 0x03, 0xFB, 0x04
        ]
    )
    idx = sample_full.find(bytes([TIME_PACKET]))
    assert idx == 0
    c_mm, mm = sample_full[1], sample_full[2]
    c_ss, ss = sample_full[3], sample_full[4]
    c_ac, ac = sample_full[5], sample_full[6]
    c_fl, fl = sample_full[7], sample_full[8]
    c_f5, p5 = sample_full[9], sample_full[10]   # filler/TO seconds pair
    c_hs, hs = sample_full[11], sample_full[12]  # home
    c_gs, gs = sample_full[13], sample_full[14]  # guest
    c_pr, pr = sample_full[15], 0x04

    assert is_complement_pair(c_mm, mm) and is_complement_pair(c_ss, ss)
    assert is_complement_pair(c_ac, ac) and is_complement_pair(c_fl, fl)
    assert is_complement_pair(c_f5, p5) and is_complement_pair(c_hs, hs) and is_complement_pair(c_gs, gs)
    assert mm == 0x08 and ss == 0x00 and ac == 0x09
    assert hs == 0x06 and gs == 0x03 and pr == 0x04

    # Test penalty packet (0x1D) decoder
    # Example: Home P1: player 5, 01:30, Home P2: player 7, 00:45
    #          Guest P1: player 3, 02:00, Guest P2: none
    sample_penalty = bytearray([
        PENALTY_PACKET,
        0xFE, 0x01,  # Home P1 minutes: 1
        0xE1, 0x1E,  # Home P1 seconds: 30
        0xFA, 0x05,  # Home P1 player: 5
        0xFF, 0x00,  # Home P2 minutes: 0
        0xD2, 0x2D,  # Home P2 seconds: 45
        0xF8, 0x07,  # Home P2 player: 7
        0xFF, 0x00,  # Home misconduct minutes: 0
        0xFF, 0x00,  # Home misconduct seconds: 0
        0xFF, 0x00,  # Home misconduct player: 0
        0xFD, 0x02,  # Guest P1 minutes: 2
        0xFF, 0x00,  # Guest P1 seconds: 0
        0xFC, 0x03,  # Guest P1 player: 3
        0xFF, 0x00,  # Guest P2 minutes: 0
        0xFF, 0x00,  # Guest P2 seconds: 0
        0xFF, 0x00,  # Guest P2 player: 0
        0xFF, 0x00,  # Guest misconduct minutes: 0
        0xFF, 0x00,  # Guest misconduct seconds: 0
        0xFF, 0x00   # Guest misconduct player: 0
    ])
    
    result = _penalty_decoder.decode_penalty_packet(sample_penalty, 0, scoreboard, state_lock)
    assert result == True, "Penalty packet decode failed"
    
    # Verify penalty data was stored correctly
    with state_lock:
        assert scoreboard["penalties"]["home"][0]["player"] == 5
        assert scoreboard["penalties"]["home"][0]["minutes"] == 1
        assert scoreboard["penalties"]["home"][0]["seconds"] == 30
        assert scoreboard["penalties"]["home"][1]["player"] == 7
        assert scoreboard["penalties"]["home"][1]["seconds"] == 45
        assert scoreboard["penalties"]["guest"][0]["player"] == 3
        assert scoreboard["penalties"]["guest"][0]["minutes"] == 2

    logging.info("All tests passed ✅ (0x02 + 0x16 + 0x1D + 0x19 + 0x1A)")
    return 0
