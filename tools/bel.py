import sys; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
HDR = """desc:GFX BEL34 [cowbell + triangle]
//tags: percussion cowbell campana triangle metal step sequencer procedural synthesis drum machine
//author: JGWizrad / Garden FX (GFX)
//
// Requires gfx-input, gfx-output, gfx-drift, gfx-ui, gfx-panel, gfx-dyn and gfx-clip (.jsfx-inc) in the same folder.
//
// BEL34. A procedural (sample-free) cowbell and triangle with a step sequencer synced to REAPER's transport.
//
//   COWBELL    the classic analogue drum-machine recipe: two band-limited square oscillators (the bell's two plate
//              modes), TUNE 300 .. 1000 Hz (587) and the OVERTONE ratio 1.3 .. 1.9 (1.44: 587 and 845 Hz), through a
//              resonant band-pass that follows the tuning (2.64 kHz at 587 Hz), with a sharp attack and a two-stage
//              decay (a fast drop, then the ring: DECAY 50 .. 1500 ms). DAMP: the hand on the bell - shorter, darker.
//   TRIANGLE   a bent steel rod struck by a beater: twelve dense, inharmonic partials from about 1.1 to 12 kHz (SIZE
//              moves them), most in close pairs that beat against each other - the shimmer; BRIGHT tilts them, RING
//              0.08 .. 0.8 s, SOFT (the beater: hard and glassy .. soft and round).
//   SEQUENCER  a lane per instrument, each with its own LENGTH (1 - 32 steps: polymeters), RATE 1/4 .. 1/32 with
//              triplets, SWING 0 - 75 %, HUMANIZE (timing late by up to 20 ms and strength by up to 30 %, at random),
//              ACCENT (accented steps louder and brighter). It follows REAPER's transport; FREE runs it at the project
//              tempo while stopped. MIDI notes play the lanes too: 56 the cowbell, 81 the triangle (open), 80 the
//              triangle muted (a short ring); velocity over 108 is an accent.
//   LEVEL / PAN per lane, MASTER. The house output stage: CLIP (ceiling -0.3 dBFS).
//   DRIFT      (0 - 100 %, 50 % = standard, 0 = none): tuning (a hair) and the player - the timing drifts a few ms
//              behind the beat and back, and the strength breathes.
//   VFD / MATRIX  the panel's look (VFD charcoal and brass; MATRIX battleship grey and cream). The look only.
//   PRESETS    12 (Init + 11) plus Reset all to defaults. A preset sets the sounds, the patterns and the groove; MASTER,
//              DRIFT and the look are left alone (Reset all restores them too).

"""
sl = sliders_common()
ls, nxt = sliders_lanes([("Cowbell",-15),("Triangle",20)])
sl += ls + """slider15:587<300,1000,1>-Cowbell tune (Hz)
slider16:1.44<1.3,1.9,0.01>-Cowbell overtone ratio
slider17:350<50,1500,1>-Cowbell decay (ms)
slider18:2<0,10,0.1>-Cowbell damp
slider19:5<0,10,0.1>-Triangle size
slider20:5<0,10,0.1>-Triangle bright
slider21:0.4<0.08,0.8,0.01>-Triangle ring (s)
slider22:3<0,10,0.1>-Triangle soft
"""
INS = r"""
NL = 2;
CBG = 0.25; TRG = 0.07;                                     // (the instruments' output trims)
#ui_man = "gfx-bel34";
// =====================================================================
// THE INSTRUMENTS
// =====================================================================
pc_nm = 12;                                           // the triangle: twelve partials, in beating pairs
TRF = 4300; TRF[0] = 1; TRF[1] = 1.0042; TRF[2] = 2.57; TRF[3] = 2.583; TRF[4] = 4.13; TRF[5] = 5.36; TRF[6] = 5.381;
TRF[7] = 6.82; TRF[8] = 8.11; TRF[9] = 8.137; TRF[10] = 9.62; TRF[11] = 11.31;
TRD = 4320; TRD[0] = 1; TRD[1] = 1; TRD[2] = 0.9; TRD[3] = 0.9; TRD[4] = 0.8; TRD[5] = 0.7; TRD[6] = 0.7; TRD[7] = 0.6; TRD[8] = 0.5; TRD[9] = 0.5; TRD[10] = 0.42; TRD[11] = 0.35;
function ins_note(n) ( pc_mute = n == 80; n == 56 ? 0 : n == 81 || n == 80 ? 1 : -1; );
function ins_srinit() ( cb_k1 = pc_kd(6); cb_kc = pc_kd(0.8); tr_kn = pc_kd(1.5); cb_khp = 1 - exp(-2 * $pi * 260 / srate); );
function pc_blep(t, dt) ( t < dt ? ( t /= dt; t + t - t * t - 1; ) : t > 1 - dt ? ( t = (t - 1) / dt; t * t + t + t + 1; ) : 0; );
function ins_trig(k, v, a) local(f0, r, b, tb, m) (
  k == 0 ? (
    cb_e1 = cb_e2 = v; cb_c = v * (a ? 1.2 : 0.8);
    cb_f1 = cb_tune * TUN[0]; cb_f2 = cb_f1 * cb_rat; cb_d1 = cb_f1 / srate; cb_d2 = cb_f2 / srate; cb_p1 = 0; cb_p2 = 0.25;
    cbf.pc_svf(2640 * (cb_f1 / 587) * (1 - 0.03 * cb_dmp) * (a ? 1 + 0.015 * pc_acc : 1), 3.2 - 0.18 * cb_dmp);
  ) : (
    f0 = 1100 * 2 ^ ((tr_sz - 5) * 0.15) * TUN[1]; r = tr_ring * (pc_mute ? 0.05 : 1); b = 0.6 + 0.08 * tr_br;
    m = 0; loop(12, md_set(m, 1, f0 * TRF[m], r * TRD[m], (m & 1 ? 0.8 : 1) * b ^ (m * 0.5) * 0.5); m += 1; );
    tr_i = v; tr_n = v * (0.15 + 0.04 * tr_br);
    tb = 16000 * 2 ^ (-tr_so * 0.32) * (a ? 1 + 0.05 * pc_acc : 1);           // the beater: soft rounds the strike off
    tr_kl = 1 - exp(-2 * $pi * min(tb, 0.45 * srate) / srate);
  );
);
function ins_block() (
  cb_tune = min(max(slider15, 300), 1000); cb_rat = min(max(slider16, 1.3), 1.9); cb_dmp = min(max(slider18, 0), 10);
  cb_k2 = pc_kd(min(max(slider17, 50), 1500) * (1 - 0.07 * cb_dmp));
  cb_kl = 1 - exp(-2 * $pi * (7000 * 2 ^ (-cb_dmp * 0.15)) / srate);
  tr_sz = min(max(slider19, 0), 10); tr_br = min(max(slider20, 0), 10); tr_ring = min(max(slider21, 0.08), 0.8); tr_so = min(max(slider22, 0), 10);
  cbf.pc_svt(); cb_e1 = pc_tn(cb_e1); cb_e2 = pc_tn(cb_e2); cb_h = pc_tn(cb_h); cb_l = pc_tn(cb_l); tr_l = pc_tn(tr_l); tr_n = pc_tn(tr_n);
);
function ins_sample() local(s1, s2, b, e, x) (
  // COWBELL: two squares (band-limited), the band-pass, the click, the two-stage decay
  cb_e2 > 0.00002 ? (
    cb_p1 += cb_d1; cb_p1 >= 1 ? cb_p1 -= 1; cb_p2 += cb_d2; cb_p2 >= 1 ? cb_p2 -= 1;
    s1 = (cb_p1 < 0.5 ? 1 : -1) + pc_blep(cb_p1, cb_d1) - pc_blep((cb_p1 + 0.5) % 1, cb_d1);
    s2 = (cb_p2 < 0.5 ? 1 : -1) + pc_blep(cb_p2, cb_d2) - pc_blep((cb_p2 + 0.5) % 1, cb_d2);
    b = cbf.pc_bp(s1 + 0.8 * s2);
    cb_h += cb_khp * (b - cb_h); b -= cb_h;
    e = 0.75 * cb_e1 + 0.25 * cb_e2; cb_e1 *= cb_k1; cb_e2 *= cb_k2;
    x = (rand(2) - 1) * cb_c; cb_c *= cb_kc;
    cb_l += cb_kl * (b * e + x * 0.5 - cb_l);
    OUT[0] = cb_l * CBG;
  );
  // TRIANGLE: the beater's strike (an impulse and the metal's noise, rounded by SOFT) rings the partials
  x = tr_i + (rand(2) - 1) * tr_n; tr_i = 0; tr_n *= tr_kn;
  tr_l += tr_kl * (x - tr_l);
  EX[1] = tr_l * TRG;
);
"""
SETS = r"""
// ---------- presets ----------
#pc_pm = "Init|Disco Cowbell|Funk Bell|Salsa Campana|Mambo Bell|Drum Machine Bell|Triangle Eighths|Forro Triangle|Shimmer|Bell and Triangle|Five Against Eight|Big Cowbell";
function bel_set(tn, rt, dc, dm, sz, br, rg, so) ( !pc_po ? (
  slider15 = tn; slider16 = rt; slider17 = dc; slider18 = dm; slider19 = sz; slider20 = br; slider21 = rg; slider22 = so;
  slider10 = 0; slider11 = -15; slider13 = 0; slider14 = 20; ); );
function load_preset(p) local(i) (
  p == 1 || p == 13 ? ( pc_seq(3, 0, 15, 5); bel_set(587, 1.44, 350, 2, 5, 5, 0.40, 3); pc_pat(0, "X.x.X.x.X.x.X.x."); pc_pat(1, "X..............."); ) :
  p == 2  ? ( pc_seq(1, 0, 10, 6); bel_set(600, 1.44, 300, 2, 5, 5, 0.40, 3); pc_pat(0, "x.X.x.X.x.X.x.X."); pc_pat(1, "................"); ) :
  p == 3  ? ( pc_seq(3, 10, 20, 6); bel_set(600, 1.5, 250, 3, 5, 5, 0.40, 3); pc_pat(0, "X..x..X...x.X..."); pc_pat(1, "................"); ) :
  p == 4  ? ( pc_seq(1, 0, 20, 7); bel_set(650, 1.42, 450, 1, 5, 5, 0.40, 3); pc_pat(0, "X.x.X.x.X.xxX.x."); pc_pat(1, "................"); ) :
  p == 5  ? ( pc_seq(1, 0, 20, 7); bel_set(700, 1.45, 400, 1.5, 5, 5, 0.40, 3); pc_pat(0, "X.xxX.x.X.xxX.x."); pc_pat(1, "................"); ) :
  p == 6  ? ( pc_seq(3, 0, 0, 5); bel_set(587, 1.44, 300, 1, 5, 5, 0.40, 3); pc_pat(0, "X..X..X.X..X..X."); pc_pat(1, "................"); ) :
  p == 7  ? ( pc_seq(1, 0, 15, 6); bel_set(587, 1.44, 350, 2, 5, 6, 0.32, 3); pc_pat(0, "................"); pc_pat(1, "X.x.X.x.X.x.X.x."); ) :
  p == 8  ? ( pc_seq(3, 8, 20, 7); bel_set(587, 1.44, 350, 2, 6, 6, 0.13, 2); pc_pat(0, "................"); pc_pat(1, "XxxXXxxXXxxXXxxX"); ) :
  p == 9  ? ( pc_seq(0, 0, 10, 4); bel_set(587, 1.44, 350, 2, 4, 7, 0.80, 4); pc_pat(0, "................"); pc_pat(1, "X..............."); ) :
  p == 10 ? ( pc_seq(1, 0, 15, 6); bel_set(600, 1.44, 300, 2, 5, 5, 0.32, 3); pc_pat(0, "X.x.X.x.X.x.X.x."); pc_pat(1, "..X...X...X...X."); ) :
  p == 11 ? ( pc_seq(1, 0, 15, 6); bel_set(620, 1.5, 300, 2, 5, 5, 0.24, 3); pc_pat(0, "X.x.x"); pc_pat(1, "X.x.x.x."); ) :
  p == 12 ? ( pc_seq(1, 0, 15, 6); bel_set(420, 1.6, 900, 0.5, 5, 5, 0.40, 3); pc_pat(0, "X.x.X.xxX.x.X.x."); pc_pat(1, "................"); );
  p == 13 && !pc_po ? ( slider5 = 0; slider6 = 0; slider7 = 50; slider8 = 0; );
  !pc_po ? ( i = 1; loop(22, ui_auto(i); i += 1; ); pr_cur = p == 13 ? 1 : p; );
);
""" + INIT_TAIL_COMMON
PANEL = r"""
kr_sect(22, pv_y, 520, 190, "COWBELL");
sprintf(#pa, "%d Hz", floor(slider15 + 0.5)); pv_k(76, pv_ky, 15, 300, 1000, 540, 1, "TUNE", #pa);
sprintf(#pb, "x %.2f", slider16); pv_k(150, pv_ky, 16, 1.3, 1.9, 1.48, 0, "OVERTONE", #pb);
sprintf(#pc, "%d ms", floor(slider17 + 0.5)); pv_k(224, pv_ky, 17, 50, 1500, 350, 1, "DECAY", #pc);
sprintf(#pd, "%.1f", slider18); pv_k(298, pv_ky, 18, 0, 10, 2, 0, "DAMP", #pd);
sprintf(#pf, "%+.1f dB", slider10); pv_k(392, pv_ky, 10, -24, 6, 0, 0, "LEVEL", #pf);
sprintf(#pg, "%+d", floor(slider11 + 0.5)); pv_k(472, pv_ky, 11, -100, 100, -15, 0, "PAN", #pg);
gfx_setfont(10); ui_col(KRI2); kr_ctxt(282, pv_y + 172, "TWO SQUARE PLATE MODES, A CLICK AND A METAL DECAY");
kr_sect(548, pv_y, 510, 190, "TRIANGLE");
sprintf(#ph, "%.1f", slider19); pv_k(600, pv_ky, 19, 0, 10, 5, 0, "SIZE", #ph);
sprintf(#pi, "%.1f", slider20); pv_k(674, pv_ky, 20, 0, 10, 5, 0, "BRIGHT", #pi);
sprintf(#pj, "%.2f s", slider21); pv_k(748, pv_ky, 21, 0.08, 0.8, 0.4, 1, "RING", #pj);
sprintf(#pk, "%.1f", slider22); pv_k(822, pv_ky, 22, 0, 10, 3, 0, "SOFT", #pk);
sprintf(#pl, "%+.1f dB", slider13); pv_k(916, pv_ky, 13, -24, 6, 0, 0, "LEVEL", #pl);
sprintf(#pm, "%+d", floor(slider14 + 0.5)); pv_k(996, pv_ky, 14, -100, 100, 20, 0, "PAN", #pm);
gfx_setfont(10); ui_col(KRI2); kr_ctxt(803, pv_y + 172, "A STEEL ROD AND ITS RINGING PARTIALS - THE BEATER'S STRIKE");
"""
build(os.path.dirname(os.path.abspath(__file__)) + '/../gfx-bel34.jsfx', HDR, sl, INS, SETS, gfx("BEL34","COWBELL AND","TRIANGLE","0xE0B64A","0xF5EAD0",["COWBELL","TRIANGLE"],PANEL))
