import sys; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
HDR = """desc:GFX CLV34 [clave, woodblocks + agogo]
//tags: percussion clave woodblock temple block agogo bell latin step sequencer procedural synthesis drum machine
//author: JGWizrad / Garden FX (GFX)
//
// Requires gfx-input, gfx-output, gfx-drift, gfx-ui, gfx-panel, gfx-dyn and gfx-clip (.jsfx-inc) in the same folder.
//
// CLV34. A procedural (sample-free) clave, a pair of woodblocks and a pair of agogo bells, each struck resonator bank
// tuned to its material, with a step sequencer synced to REAPER's transport.
//
//   CLAVE      two hardwood sticks: a bright, short, pitched knock (TUNE 1.5 .. 3.5 kHz) with the bar's upper modes
//              (x 2.78, 7.38: a free hardwood bar). DECAY. LAST +1/16 moves the pattern's last hit a 16th later (the
//              traditional push on the son and rumba claves); off moves it back. The clave presets run two bars of 16ths.
//   WOODBLOCK  a hollow block, high and low (the low about a fifth down): its cavity's closely spaced modes (x 1.78,
//              2.38, 3.38) and the knock of the stick. TUNE 500 .. 1500 Hz (the high block), DECAY.
//   AGOGO      two iron cone bells, high and low (a fourth apart): widely spread inharmonic modes (x 4.08, 6.67 and
//              a fixed 3.7 kHz shell ring), a slow beat between the near-doubled fundamental, a long ring.
//              TUNE 600 .. 1600 Hz (the high bell), DECAY.
//   HARDNESS   the stick's contact: a soft stick stays on the wood longer (a wider, rounder strike), a hard one
//              bounces off at once (bright). Accents a little harder still.
//   SEQUENCER  a lane per voice (CLAVE, WOOD HI, WOOD LO, AGOGO HI, AGOGO LO), each with its own LENGTH (1 - 32 steps:
//              polymeters), RATE 1/4 .. 1/32 with triplets, SWING 0 - 75 %, HUMANIZE (timing late by up to 20 ms and
//              strength by up to 30 %, at random), ACCENT. It follows REAPER's transport; FREE runs it at the project
//              tempo while stopped. MIDI notes play the lanes too: 75 claves, 76 / 77 woodblocks high / low, 67 / 68
//              agogo high / low; velocity over 108 is an accent.
//   LEVEL / PAN per lane, MASTER. The house output stage: CLIP (ceiling -0.3 dBFS).
//   DRIFT      (0 - 100 %, 50 % = standard, 0 = none): tuning (a hair) and the player - the timing drifts a few ms
//              behind the beat and back, and the strength breathes.
//   VFD / MATRIX  the panel's look (VFD charcoal and rosewood; MATRIX battleship grey and cream). The look only.
//   PRESETS    12 (Init + 11) plus Reset all to defaults. A preset sets the sounds, the patterns and the groove; MASTER,
//              DRIFT and the look are left alone (Reset all restores them too).

"""
sl = sliders_common()
ls, nxt = sliders_lanes([("Clave",0,32),("Wood hi",-30),("Wood lo",-40),("Agogo hi",30),("Agogo lo",40)])
sl += ls + """slider24:2400<1500,3500,1>-Clave tune (Hz)
slider25:0.5<0.15,0.95,0.01>-Clave decay
slider26:950<500,1500,1>-Woodblock tune (Hz)
slider27:0.45<0.15,0.85,0.01>-Woodblock decay
slider28:950<600,1600,1>-Agogo tune (Hz)
slider29:0.16<0.08,0.24,0.01>-Agogo decay
slider30:6<0,10,0.1>-Hardness
slider31:0<0,1,1{Off,On}>-Clave last hit a 16th late
"""
INS = r"""
NL = 5;
CVK = 4250; CVK[0] = 0.52; CVK[1] = 0.344; CVK[2] = 0.272; CVK[3] = 0.226; CVK[4] = 0.286;   // (each voice's output trim)
#ui_man = "gfx-clv34";
cv_lap = 0;                                           // (LATE LAST as applied to the pattern)
XN = 4210; XD = 4240; XW = 4260; XP = 4270; XA = 4280; XH = 4290;   // per lane: the knock and its decay; the stick's pulse
// =====================================================================
// THE INSTRUMENTS - every voice a struck bank of resonators (modes 0-1 clave, 2-4 / 5-7 woodblocks, 8-11 / 12-15 agogo)
// =====================================================================
pc_nm = 16;
function ins_note(n) ( pc_mute = 0; n == 75 ? 0 : n == 76 ? 1 : n == 77 ? 2 : n == 67 ? 3 : n == 68 ? 4 : -1; );
function ins_srinit() ( XD[0] = pc_kd(0.5); XD[1] = XD[2] = pc_kd(2.5); XD[3] = XD[4] = pc_kd(0.6); );
function ins_trig(k, v, a) local(f, d, m, h) (
  k == 0 ? (
    f = cv_ct * TUN[0]; d = cv_cd;                    // CLAVE: a free hardwood bar
    md_set(0, 0, f, 0.065 * d, 1); md_set(1, 0, f * 2.777, 0.022 * d, 0.3);
  ) : k <= 2 ? (
    f = cv_wt * (k == 2 ? 0.68 : 1) * TUN[k]; d = cv_wd; m = k == 1 ? 2 : 5;   // WOODBLOCK: the cavity's modes
    md_set(m, k, f, 0.07 * d, 1); md_set(m + 1, k, f * 1.777, 0.045 * d, 0.55); md_set(m + 2, k, f * 2.378, 0.03 * d, 0.35);
  ) : (
    f = cv_at * (k == 4 ? 0.75 : 1) * TUN[k]; d = cv_ad; m = k == 3 ? 8 : 12;  // AGOGO: an iron cone
    md_set(m, k, f, 0.4 * d, 1); md_set(m + 1, k, f * 1.0035, 0.36 * d, 0.6); md_set(m + 2, k, f * 4.08, 0.17 * d, 0.45);
    md_set(m + 3, k, f * 6.669, 0.09 * d, 0.3);
  );
  // the stick: a raised-cosine contact, narrower for harder sticks (and accents)
  h = (0.75 - 0.06 * cv_hd) * (a ? 1 - 0.04 * pc_acc : 1) / f;                    // (s: a fraction of the voice's period)
  XW[k] = max(floor(h * srate), 2); XP[k] = 0; XA[k] = v * 2 / XW[k];
  XN[k] = v * (k == 1 || k == 2 ? 0.5 : k == 0 ? 0.25 : 0.12);                     // and its knock
);
// LATE LAST: the clave's last hit a 16th late (the traditional push on the son and rumba claves). It moves the hit in
// the pattern itself, so the grid shows what plays; switching it off moves it back.
function cv_shift(dir) local(n, i, l) (
  n = min(max(floor(slider9 + 0.5), 1), 32); l = -1; i = 0; loop(n, STP[i] > 0 ? l = i; i += 1; );
  dir > 0 ? ( l >= 0 && l + 1 < n && STP[l + 1] === 0 ? ( STP[l + 1] = STP[l]; STP[l] = 0; ); )
          : ( l >= 1 && STP[l - 1] === 0 ? ( STP[l - 1] = STP[l]; STP[l] = 0; ); );
);
function ins_block() (
  cv_lt = slider31 >= 0.5; cv_lt != cv_lap ? ( cv_shift(cv_lt ? 1 : -1); cv_lap = cv_lt; );
  cv_ct = min(max(slider24, 1500), 3500); cv_cd = min(max(slider25, 0.15), 0.95);
  cv_wt = min(max(slider26, 500), 1500); cv_wd = min(max(slider27, 0.15), 0.85);
  cv_at = min(max(slider28, 600), 1600); cv_ad = min(max(slider29, 0.08), 0.24);
  cv_hd = min(max(slider30, 0), 10);
  pc_k = 0; loop(NL, XN[pc_k] = pc_tn(XN[pc_k]); XH[pc_k] = pc_tn(XH[pc_k]); pc_k += 1; );
);
function ins_sample() local(k, x, n) (
  k = 0;
  loop(NL,
    x = 0;
    XP[k] < XW[k] ? ( x = XA[k] * (0.5 - 0.5 * cos(2 * $pi * XP[k] / XW[k])); XP[k] += 1; );   // the stick on the wood
    n = (rand(2) - 1) * XN[k]; XN[k] *= XD[k]; XH[k] += 0.5 * (n - XH[k]);                  // the knock (high-passed)
    EX[k] = x * CVK[k];
    OUT[k] += (n - XH[k]) * CVK[k] * 0.4;
    k += 1;
  );
);
"""
SETS = r"""
// ---------- presets ----------
#pc_pm = "Init|Son Clave 2-3|Rumba Clave|Bossa Clave|Woodblock Tick|Agogo Samba|Afro Bell 12/8|Cha Cha|Temple Blocks|Clave and Bell|Polymeter|Batucada Lite";
function clv_set(ct, cd, wt, wd, at, ad, hd) ( !pc_po ? (
  slider24 = ct; slider25 = cd; slider26 = wt; slider27 = wd; slider28 = at; slider29 = ad; slider30 = hd;
  slider31 = 0; cv_lap = 0; slider10 = slider13 = slider16 = slider19 = slider22 = 0; slider11 = 0; slider14 = -30; slider17 = -40; slider20 = 30; slider23 = 40; ); );
function clv_none() ( pc_pat(1, "................"); pc_pat(2, "................"); pc_pat(3, "................"); pc_pat(4, "................"); );
function load_preset(p) local(i) (
  p == 1 || p == 13 ? ( pc_seq(3, 0, 15, 5); clv_set(2400, 0.5, 950, 0.45, 950, 0.16, 6); pc_pat(0, "X.....X.....X.......X...X......."); clv_none(); ) :
  p == 2  ? ( pc_seq(3, 0, 15, 5); clv_set(2400, 0.5, 950, 0.45, 950, 0.16, 6); pc_pat(0, "....X...X.......X.....X.....X..."); clv_none(); ) :
  p == 3  ? ( pc_seq(3, 0, 15, 5); clv_set(2300, 0.55, 950, 0.45, 950, 0.16, 6); pc_pat(0, "X.....X.......X.....X...X......."); clv_none(); ) :
  p == 4  ? ( pc_seq(3, 0, 10, 4); clv_set(2200, 0.45, 950, 0.45, 950, 0.16, 5); pc_pat(0, "X.....X.....X.......X.....X....."); clv_none(); ) :
  p == 5  ? ( pc_seq(3, 0, 15, 6); clv_set(2400, 0.5, 1000, 0.45, 950, 0.16, 7); pc_pat(0, "................"); clv_none();
              pc_pat(1, "x.x.x.x.x.x.x.x."); pc_pat(2, "X.......X......."); ) :
  p == 6  ? ( pc_seq(3, 5, 20, 6); clv_set(2400, 0.5, 950, 0.45, 900, 0.17, 6); pc_pat(0, "................"); clv_none();
              pc_pat(3, "X.X..X.X.X..X.X."); pc_pat(4, ".X..X...X.X..X.."); ) :
  p == 7  ? ( pc_seq(2, 0, 15, 6); clv_set(2400, 0.5, 950, 0.45, 1000, 0.19, 7); pc_pat(0, "............"); clv_none();
              pc_pat(3, "X.X.XX.X.X.X"); pc_pat(4, "............"); ) :
  p == 8  ? ( pc_seq(3, 0, 15, 5); clv_set(2400, 0.5, 900, 0.45, 950, 0.16, 6); pc_pat(0, "................"); clv_none();
              pc_pat(1, "X..x..X.X..x..X."); pc_pat(2, "...x.......x...."); ) :
  p == 9  ? ( pc_seq(3, 0, 20, 5); clv_set(2400, 0.5, 800, 0.7, 950, 0.16, 4); pc_pat(0, "................"); clv_none();
              pc_pat(1, "X...x.x...X.x..."); pc_pat(2, "..x...X.x...x.X."); ) :
  p == 10 ? ( pc_seq(3, 0, 15, 6); clv_set(2400, 0.5, 950, 0.45, 950, 0.16, 6); pc_pat(0, "X.....X.....X.......X...X......."); clv_none();
              pc_pat(3, "X...X...X...X.X.X...X...X...X.X."); pc_pat(4, "..X...X...X.......X...X...X....."); ) :
  p == 11 ? ( pc_seq(3, 0, 15, 6); clv_set(2400, 0.5, 950, 0.45, 950, 0.16, 6); pc_pat(0, "X.....X.....X.......X...X......."); clv_none();
              pc_pat(1, "x...x...x...X."); pc_pat(3, "X...x...x...X...x...x..."); ) :
  p == 12 ? ( pc_seq(3, 8, 25, 7); clv_set(2500, 0.5, 1000, 0.45, 950, 0.16, 8); pc_pat(0, "....X...X.......X.....X.....X..."); clv_none();
              pc_pat(1, "x...x.x.x...x.x.x...x.x.x...x.x."); pc_pat(2, "X...............X..............."); pc_pat(3, "X...X.....X...X...X.....X...X..."); pc_pat(4, "..X.....X.......X...X.....X....."); );
  p == 13 && !pc_po ? ( slider5 = 0; slider6 = 0; slider7 = 50; slider8 = 0; );
  !pc_po ? ( i = 1; loop(31, ui_auto(i); i += 1; ); pr_cur = p == 13 ? 1 : p; );
);
""" + INIT_TAIL_COMMON
PANEL = r"""
kr_sect(22, pv_y, 290, 190, "CLAVE");
kr_key(206, pv_y + 8, 98, 20, "LAST +1/16", slider31 >= 0.5) ? kr_tog(31);
sprintf(#pa, "%d Hz", floor(slider24 + 0.5)); pv_k(60, pv_ky, 24, 1500, 3500, 2400, 1, "TUNE", #pa);
sprintf(#pb, "x %.2f", slider25); pv_k(116, pv_ky, 25, 0.15, 0.95, 0.5, 1, "DECAY", #pb);
sprintf(#pc, "%+.1f dB", slider10); pv_k(172, pv_ky, 10, -24, 6, 0, 0, "LEVEL", #pc);
sprintf(#pd, "%+d", floor(slider11 + 0.5)); pv_k(228, pv_ky, 11, -100, 100, 0, 0, "PAN", #pd);
sprintf(#pe, "%.1f", slider30); pv_k(284, pv_ky, 30, 0, 10, 6, 0, "HARD", #pe);
gfx_setfont(10); ui_col(KRI2); kr_ctxt(167, pv_y + 172, "HARDWOOD STICKS");
function pv_pair(x, tu, de, l1, l2, p1, p2, dt, dp1, dp2, nm, sub) (
  kr_sect(x, pv_y, 368, 190, nm);
  sprintf(#pv1, "%d Hz", floor(slider(tu) + 0.5)); pv_k(x + 40, pv_ky, tu, nm == "AGOGO" ? 600 : 500, nm == "AGOGO" ? 1600 : 1500, dt, 1, "TUNE", #pv1);
  sprintf(#pv2, "x %.2f", slider(de)); de === 27 ? pv_k(x + 96, pv_ky, de, 0.15, 0.85, 0.45, 1, "DECAY", #pv2) : pv_k(x + 96, pv_ky, de, 0.08, 0.24, 0.16, 1, "DECAY", #pv2);
  sprintf(#pv3, "%+.1f", slider(l1)); pv_k(x + 152, pv_ky, l1, -24, 6, 0, 0, "HI LVL", #pv3);
  sprintf(#pv4, "%+.1f", slider(l2)); pv_k(x + 208, pv_ky, l2, -24, 6, 0, 0, "LO LVL", #pv4);
  sprintf(#pv5, "%+d", floor(slider(p1) + 0.5)); pv_k(x + 264, pv_ky, p1, -100, 100, dp1, 0, "HI PAN", #pv5);
  sprintf(#pv6, "%+d", floor(slider(p2) + 0.5)); pv_k(x + 320, pv_ky, p2, -100, 100, dp2, 0, "LO PAN", #pv6);
  gfx_setfont(10); ui_col(KRI2); kr_ctxt(x + 184, pv_y + 172, sub);
);
pv_pair(318, 26, 27, 13, 16, 14, 17, 950, -30, -40, "WOODBLOCK", "A HOLLOW BLOCK, HIGH AND LOW");
pv_pair(690, 28, 29, 19, 22, 20, 23, 950, 30, 40, "AGOGO", "TWO IRON BELLS, HIGH AND LOW");
"""
build(os.path.dirname(os.path.abspath(__file__)) + '/../gfx-clv34.jsfx', HDR, sl, INS, SETS, gfx("CLV34","CLAVE, WOODBLOCKS","AND AGOGO","0xC27A5A","0xF3E2D8",["CLAVE","WOOD HI","WOOD LO","AGOGO HI","AGOGO LO"],PANEL))
