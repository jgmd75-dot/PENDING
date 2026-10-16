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
//   CLAVE      two hardwood sticks: a bright, short, pitched click (TUNE 1.5 .. 3.5 kHz) and its upper mode. DECAY.
//   WOODBLOCK  a hollow block, high and low (the low a fifth or so down): three modes and the knock of the stick.
//              TUNE 500 .. 1500 Hz (the high block), DECAY.
//   AGOGO      two iron bells, high and low (the low a fourth down): four inharmonic modes and a longer ring.
//              TUNE 600 .. 1600 Hz (the high bell), DECAY.
//   HARDNESS   the stick or beater: soft and woody .. hard and bright (accents a little harder still).
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
ls, nxt = sliders_lanes([("Clave",0),("Wood hi",-30),("Wood lo",-40),("Agogo hi",30),("Agogo lo",40)])
sl += ls + """slider24:2400<1500,3500,1>-Clave tune (Hz)
slider25:1<0.3,3,0.01>-Clave decay
slider26:950<500,1500,1>-Woodblock tune (Hz)
slider27:1<0.3,3,0.01>-Woodblock decay
slider28:950<600,1600,1>-Agogo tune (Hz)
slider29:1<0.3,3,0.01>-Agogo decay
slider30:6<0,10,0.1>-Hardness
"""
INS = r"""
NL = 5;
CVK = 4250; CVK[0] = 0.23; CVK[1] = 0.115; CVK[2] = 0.069; CVK[3] = 0.13; CVK[4] = 0.17;   // (each voice's output trim)
#ui_man = "gfx-clv34";
XI = 4200; XN = 4210; XL = 4220; XK = 4230; XD = 4240;   // per lane: the strike's impulse, noise, its low-pass, decay
// =====================================================================
// THE INSTRUMENTS - every voice a struck bank of resonators (modes 0-1 clave, 2-4 / 5-7 woodblocks, 8-11 / 12-15 agogo)
// =====================================================================
pc_nm = 16;
function ins_note(n) ( pc_mute = 0; n == 75 ? 0 : n == 76 ? 1 : n == 77 ? 2 : n == 67 ? 3 : n == 68 ? 4 : -1; );
function ins_srinit() ( XD[0] = pc_kd(0.4); XD[1] = XD[2] = pc_kd(1.6); XD[3] = XD[4] = pc_kd(0.6); );
function ins_trig(k, v, a) local(f, d, m, h) (
  k == 0 ? (
    f = cv_ct * TUN[0]; d = cv_cd;
    md_set(0, 0, f, 0.07 * d, 1); md_set(1, 0, f * 2.53, 0.03 * d, 0.35);
  ) : k <= 2 ? (
    f = cv_wt * (k == 2 ? 0.68 : 1) * TUN[k]; d = cv_wd; m = k == 1 ? 2 : 5;
    md_set(m, k, f, 0.06 * d, 1); md_set(m + 1, k, f * 2.3, 0.035 * d, 0.5); md_set(m + 2, k, f * 3.75, 0.02 * d, 0.25);
  ) : (
    f = cv_at * (k == 4 ? 0.75 : 1) * TUN[k]; d = cv_ad; m = k == 3 ? 8 : 12;
    md_set(m, k, f, 0.55 * d, 1); md_set(m + 1, k, f * 2.62, 0.35 * d, 0.6); md_set(m + 2, k, f * 4.35, 0.2 * d, 0.35); md_set(m + 3, k, f * 5.9, 0.12 * d, 0.2);
  );
  XI[k] = v; XN[k] = v * (k == 1 || k == 2 ? 0.6 : 0.3);
  h = 2500 * 2 ^ (cv_hd * 0.28) * (a ? 1 + 0.06 * pc_acc : 1);                    // HARDNESS: the strike's brightness
  XK[k] = 1 - exp(-2 * $pi * min(h, 0.45 * srate) / srate);
);
function ins_block() (
  cv_ct = min(max(slider24, 1500), 3500); cv_cd = min(max(slider25, 0.3), 3);
  cv_wt = min(max(slider26, 500), 1500); cv_wd = min(max(slider27, 0.3), 3);
  cv_at = min(max(slider28, 600), 1600); cv_ad = min(max(slider29, 0.3), 3);
  cv_hd = min(max(slider30, 0), 10);
  pc_k = 0; loop(NL, XL[pc_k] = pc_tn(XL[pc_k]); XN[pc_k] = pc_tn(XN[pc_k]); pc_k += 1; );
);
function ins_sample() local(k, x) (
  k = 0;
  loop(NL,
    x = XI[k] + (rand(2) - 1) * XN[k]; XI[k] = 0; XN[k] *= XD[k];
    XL[k] += XK[k] * (x - XL[k]);
    EX[k] = XL[k] * CVK[k];
    k += 1;
  );
);
"""
SETS = r"""
// ---------- presets ----------
#pc_pm = "Init|Son Clave 2-3|Rumba Clave|Bossa Clave|Woodblock Tick|Agogo Samba|Afro Bell 12/8|Cha Cha|Temple Blocks|Clave and Bell|Polymeter|Batucada Lite";
function clv_set(ct, cd, wt, wd, at, ad, hd) ( !pc_po ? (
  slider24 = ct; slider25 = cd; slider26 = wt; slider27 = wd; slider28 = at; slider29 = ad; slider30 = hd;
  slider10 = slider13 = slider16 = slider19 = slider22 = 0; slider11 = 0; slider14 = -30; slider17 = -40; slider20 = 30; slider23 = 40; ); );
function clv_none() ( pc_pat(1, "................"); pc_pat(2, "................"); pc_pat(3, "................"); pc_pat(4, "................"); );
function load_preset(p) local(i) (
  p == 1 || p == 13 ? ( pc_seq(3, 0, 15, 5); clv_set(2400, 1, 950, 1, 950, 1, 6); pc_pat(0, "X..X..X...X.X..."); clv_none(); ) :
  p == 2  ? ( pc_seq(3, 0, 15, 5); clv_set(2400, 1, 950, 1, 950, 1, 6); pc_pat(0, "..X.X...X..X..X."); clv_none(); ) :
  p == 3  ? ( pc_seq(3, 0, 15, 5); clv_set(2300, 1.1, 950, 1, 950, 1, 6); pc_pat(0, "X..X...X..X.X..."); clv_none(); ) :
  p == 4  ? ( pc_seq(3, 0, 10, 4); clv_set(2200, 0.9, 950, 1, 950, 1, 5); pc_pat(0, "X..X..X...X..X.."); clv_none(); ) :
  p == 5  ? ( pc_seq(3, 0, 15, 6); clv_set(2400, 1, 1000, 1, 950, 1, 7); pc_pat(0, "................"); clv_none();
              pc_pat(1, "x.x.x.x.x.x.x.x."); pc_pat(2, "X.......X......."); ) :
  p == 6  ? ( pc_seq(3, 5, 20, 6); clv_set(2400, 1, 950, 1, 900, 1.1, 6); pc_pat(0, "................"); clv_none();
              pc_pat(3, "X.X..X.X.X..X.X."); pc_pat(4, ".X..X...X.X..X.."); ) :
  p == 7  ? ( pc_seq(2, 0, 15, 6); clv_set(2400, 1, 950, 1, 1000, 1.2, 7); pc_pat(0, "............"); clv_none();
              pc_pat(3, "X.X.XX.X.X.X"); pc_pat(4, "............"); ) :
  p == 8  ? ( pc_seq(3, 0, 15, 5); clv_set(2400, 1, 900, 1, 950, 1, 6); pc_pat(0, "................"); clv_none();
              pc_pat(1, "X..x..X.X..x..X."); pc_pat(2, "...x.......x...."); ) :
  p == 9  ? ( pc_seq(3, 0, 20, 5); clv_set(2400, 1, 800, 1.6, 950, 1, 4); pc_pat(0, "................"); clv_none();
              pc_pat(1, "X...x.x...X.x..."); pc_pat(2, "..x...X.x...x.X."); ) :
  p == 10 ? ( pc_seq(3, 0, 15, 6); clv_set(2400, 1, 950, 1, 950, 1, 6); pc_pat(0, "X..X..X...X.X..."); clv_none();
              pc_pat(3, "X.X.X.XXX.X.X.XX"); pc_pat(4, ".X.X.X...X.X.X.."); ) :
  p == 11 ? ( pc_seq(3, 0, 15, 6); clv_set(2400, 1, 950, 1, 950, 1, 6); pc_pat(0, "X..X..X...X.X..."); clv_none();
              pc_pat(1, "x.x.x.X"); pc_pat(3, "X.x.x.X.x.x."); ) :
  p == 12 ? ( pc_seq(3, 8, 25, 7); clv_set(2500, 1, 1000, 1, 950, 1, 8); pc_pat(0, "..X.X...X..X..X."); clv_none();
              pc_pat(1, "x.xxx.xxx.xxx.xx"); pc_pat(2, "X.......X......."); pc_pat(3, "X.X..X.X.X..X.X."); pc_pat(4, ".X..X...X.X..X.."); );
  p == 13 && !pc_po ? ( slider5 = 0; slider6 = 0; slider7 = 50; slider8 = 0; );
  !pc_po ? ( i = 1; loop(30, ui_auto(i); i += 1; ); pr_cur = p == 13 ? 1 : p; );
);
""" + INIT_TAIL_COMMON
PANEL = r"""
kr_sect(22, pv_y, 290, 190, "CLAVE");
sprintf(#pa, "%d Hz", floor(slider24 + 0.5)); pv_k(60, pv_ky, 24, 1500, 3500, 2400, 1, "TUNE", #pa);
sprintf(#pb, "x %.2f", slider25); pv_k(116, pv_ky, 25, 0.3, 3, 1, 1, "DECAY", #pb);
sprintf(#pc, "%+.1f dB", slider10); pv_k(172, pv_ky, 10, -24, 6, 0, 0, "LEVEL", #pc);
sprintf(#pd, "%+d", floor(slider11 + 0.5)); pv_k(228, pv_ky, 11, -100, 100, 0, 0, "PAN", #pd);
sprintf(#pe, "%.1f", slider30); pv_k(284, pv_ky, 30, 0, 10, 6, 0, "HARD", #pe);
gfx_setfont(10); ui_col(KRI2); kr_ctxt(167, pv_y + 172, "HARDWOOD STICKS");
function pv_pair(x, tu, de, l1, l2, p1, p2, dt, dp1, dp2, nm, sub) (
  kr_sect(x, pv_y, 368, 190, nm);
  sprintf(#pv1, "%d Hz", floor(slider(tu) + 0.5)); pv_k(x + 40, pv_ky, tu, nm == "AGOGO" ? 600 : 500, nm == "AGOGO" ? 1600 : 1500, dt, 1, "TUNE", #pv1);
  sprintf(#pv2, "x %.2f", slider(de)); pv_k(x + 96, pv_ky, de, 0.3, 3, 1, 1, "DECAY", #pv2);
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
