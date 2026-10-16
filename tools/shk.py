import sys; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
HDR = """desc:GFX G SHK34 [shakers + tambourine]
//tags: percussion shaker egg maracas tambourine step sequencer procedural synthesis drum machine
//author: JGWizrad / Garden FX (GFX)
//
// Requires gfx-input, gfx-output, gfx-drift, gfx-ui, gfx-panel, gfx-dyn and gfx-clip (.jsfx-inc) in the same folder.
//
// SHK34. Procedural (sample-free) shakers and tambourine with a step sequencer synced to REAPER's transport.
//
//   SHAKER     each hit is a shake stroke: a cloud of tiny grains (the beads hitting each other and the shell) firing
//              at random, swelling and dying with the stroke, through two resonant band-passes (the shell). Strokes
//              alternate push and pull (PUSH/PULL: how much weaker and darker the pull is). TONE 1.5 .. 9 kHz (egg
//              shakers high, wooden maracas low), BEADS (small and dense .. big and sparse), STROKE 30 .. 400 ms,
//              RESONANCE (the shell's ring).
//   TAMBOURINE the jingles as a stochastic cloud too: the hit sets them moving (its energy dies away over RING,
//              40 .. 800 ms), and at random moments they collide - each collision a burst that rings the jingles' metal
//              resonances (about 5.6 and 8.1 kHz, and the shell's 2.3 kHz; BRIGHT moves them), retuned a little at every
//              collision as the jingles tilt: the shimmer. RATTLE: how many jingles; HIT: the frame's click.
//   SEQUENCER  a lane per instrument, each with its own LENGTH (1 - 32 steps: polymeters), RATE 1/4 .. 1/32 with
//              triplets, SWING 0 - 75 % (the off-steps late; 33 % is a triplet feel), HUMANIZE (timing late by up to
//              20 ms and strength by up to 30 %, at random), ACCENT (accented steps louder and brighter). It follows
//              REAPER's transport; FREE runs it at the project tempo while stopped. MIDI notes play the lanes too:
//              70 (maracas) and 82 (shaker) the shaker, 54 the tambourine; velocity over 108 is an accent.
//   LEVEL / PAN per lane, MASTER. The house output stage: CLIP (ceiling -0.3 dBFS).
//   DRIFT      (0 - 100 %, 50 % = standard, 0 = none): tuning (a hair) and the player - the timing drifts a few ms
//              behind the beat and back, and the strength breathes.
//   VFD / MATRIX  the panel's look (VFD charcoal and sand; MATRIX battleship grey and cream). The look only.
//   REVERB     on the whole mix: ROOM, SPRING (two tanks with the chirp) or PLATE; DECAY, TONE and AMOUNT (added
//              to the dry). Switching type fades across without a click. Presets leave it alone; Reset all clears it.
//   PRESETS    12 (Init + 11) plus Reset all to defaults. A preset sets the sounds, the patterns and the groove; MASTER,
//              DRIFT and the look are left alone (Reset all restores them too).

"""
sl = sliders_common()
ls, nxt = sliders_lanes([("Shaker",-20),("Tambourine",25)])
sl += ls + """slider15:5500<1500,9000,1>-Shaker tone (Hz)
slider16:4<0,10,0.1>-Shaker beads
slider17:110<30,400,1>-Shaker stroke (ms)
slider18:4<0,10,0.1>-Shaker resonance
slider19:4<0,10,0.1>-Shaker push / pull
slider20:250<40,800,1>-Tambourine ring (ms)
slider21:5<0,10,0.1>-Tambourine bright
slider22:5<0,10,0.1>-Tambourine hit
slider23:5<0,10,0.1>-Tambourine rattle
"""
INS = r"""
NL = 2;
SHG = 0.45; TBG = 0.24;                                     // (the instruments' output trims)
#ui_man = "gfx-g-shk34";
// =====================================================================
// THE INSTRUMENTS
// =====================================================================
pc_nm = 8;                                            // the tambourine: the shell and a fixed bank of detuned jingle pairs
function ins_note(n) ( pc_mute = 0; n == 70 || n == 82 ? 0 : n == 54 ? 1 : -1; );
function ins_srinit() ( tb_ks = pc_kd(1.4); tb_kc = pc_kd(0.25); tb_pc = 22050 / srate / 1024; );
function ins_trig(k, v, a) local(b, r) (
  k == 0 ? (
    sh_dir = 1 - sh_dir;                              // push, pull, push ...
    sh_tg = v * (sh_dir ? 1 : 1 - 0.05 * sh_pp); sh_at = 1;
    sh_f = sh_tone * (sh_dir ? 1 : 1 - 0.008 * sh_pp) * (a ? 1 + 0.012 * pc_acc : 1) * TUN[0];
    s1.pc_svf(sh_f, sh_q); s2.pc_svf(sh_f * 1.6, sh_q * 0.8);
  ) : (
    tb_E += v * (a ? 1 + 0.05 * pc_acc : 1);           // the shake's energy
    tb_c = v * tb_hit;                                 // the frame's click
  );
);
function ins_block() (
  sh_tone = min(max(slider15, 1500), 9000); sh_bd = min(max(slider16, 0), 10); sh_len = min(max(slider17, 30), 400);
  sh_q = 1 + 0.9 * min(max(slider18, 0), 10); sh_pp = min(max(slider19, 0), 10);
  sh_ka = pc_tc(6); sh_kd = pc_kd(sh_len * 0.45);
  sh_den = (7000 - 550 * sh_bd) / srate; sh_kg = pc_kd(0.15 + 0.25 * sh_bd);
  sh_mk = 0.9 / sqrt(sh_q);
  tb_ring = min(max(slider20, 40), 800); tb_br = min(max(slider21, 0), 10); tb_hit = min(max(slider22, 0), 10) / 5;
  tb_rt = min(max(slider23, 0), 10) / 10; tb_kE = pc_kd(tb_ring * 0.5);
  tb_nob = 8 + 40 * tb_rt;                           // the jingles in play
  tb_gn = sqrt(250 / max(tb_ring, 120)) * (28 / tb_nob) ^ 0.25; // (the level kept as RING and RATTLE change)
  // the jingles: a fixed bank of slightly detuned pairs that ring cleanly (retuning a ringing mode crackles)
  tb_bs = (0.8 + 0.04 * tb_br) * TUN[1]; tb_jt = 0.010 + 0.012 * tb_rt;
  md_setn(0, 1, 2300 * tb_bs, 0.0016, 0.10 * TBG);
  md_setn(1, 1, 5470 * tb_bs, tb_jt, 0.55 * TBG);
  md_setn(2, 1, 5730 * tb_bs, tb_jt * 0.9, 0.55 * TBG);
  md_setn(3, 1, 7860 * tb_bs, tb_jt * 0.8, 0.6 * TBG);
  md_setn(4, 1, 8120 * tb_bs, tb_jt * 0.85, 0.6 * TBG);
  md_setn(5, 1, 8410 * tb_bs, tb_jt * 0.75, 0.45 * TBG);
  md_setn(6, 1, 10950 * tb_bs, tb_jt * 0.6, (0.08 + 0.03 * tb_br) * TBG);
  md_setn(7, 1, 11650 * tb_bs, tb_jt * 0.55, (0.08 + 0.03 * tb_br) * TBG);
  s1.pc_svt(); s2.pc_svt(); sh_e = pc_tn(sh_e); sh_g = pc_tn(sh_g); tb_E = pc_tn(tb_E); tb_L = pc_tn(tb_L); tb_hp = pc_tn(tb_hp);
);
function ins_sample() local(n, x) (
  // SHAKER: the stroke, its grain cloud, the shell
  sh_at ? ( sh_e += (sh_tg - sh_e) * sh_ka; sh_e >= sh_tg * 0.95 ? sh_at = 0; ) : sh_e *= sh_kd;
  sh_e > 0.0001 ? (
    rand(1) < sh_den * min(sh_e * 1.6, 1) ? sh_g = max(sh_g, (0.35 + rand(0.65)) * sh_e);
    sh_g *= sh_kg;
    n = (rand(2) - 1) * sh_g;
    OUT[0] = (s1.pc_bp(n) + 0.55 * s2.pc_bp(n) + 0.12 * n) * sh_mk * SHG;
  );
  // TAMBOURINE (PhISEM): collisions at random while the shake's energy lasts, thinning out as it dies away;
  // each collision's strength follows the energy on a gentle curve, so the jingles fade out rather than stop
  tb_E > 0.00005 ? (
    rand(1) < tb_nob * tb_pc * (0.3 + 0.7 * min(tb_E, 1)) ? tb_L = max(tb_L, (0.55 + rand(0.45)) * tb_E ^ 0.7 * tb_gn);
    tb_E *= tb_kE;
  );
  x = (rand(2) - 1) * tb_L; tb_L *= tb_ks;
  EX[1] = x;
  x = (rand(2) - 1) * tb_c; tb_hp += 0.45 * (x - tb_hp); OUT[1] += (x - tb_hp) * 0.6 * TBG; tb_c *= tb_kc;   // the frame's click
);
"""
SETS = r"""
// ---------- presets ----------
#pc_pm = "Init|Egg Shaker 16ths|Samba Ganza|Pop Tambourine|Motown Fours|Soul Sixteenths|Swing Shuffle|Maracas|Three Over Four|Bossa Shaker|Halftime|Busy Groove";
function shk_set(tn, bd, st, rs, pp, rg, br, ht, rt) ( !pc_po ? (
  slider15 = tn; slider16 = bd; slider17 = st; slider18 = rs; slider19 = pp; slider20 = rg; slider21 = br; slider22 = ht; slider23 = rt;
  slider10 = 0; slider11 = -20; slider13 = 0; slider14 = 25; ); );
function load_preset(p) local(i) (
  p == 1 || p == 13 ? ( pc_seq(3, 0, 15, 5); shk_set(5500, 4, 110, 4, 4, 250, 5, 5, 5); pc_pat(0, "XxxxXxxxXxxxXxxx"); pc_pat(1, "....X.......X..."); ) :
  p == 2  ? ( pc_seq(3, 8, 20, 6); shk_set(7200, 2, 80, 3, 3, 250, 5, 5, 5); pc_pat(0, "XxxxXxxxXxxxXxxx"); pc_pat(1, "................"); ) :
  p == 3  ? ( pc_seq(3, 12, 20, 7); shk_set(4300, 6, 120, 5, 6, 250, 5, 5, 5); pc_pat(0, "XxxXXxxXXxxXXxxX"); pc_pat(1, ".......x.......X"); ) :
  p == 4  ? ( pc_seq(3, 0, 15, 6); shk_set(5500, 4, 110, 4, 4, 300, 6, 6, 6); pc_pat(0, "................"); pc_pat(1, "x.x.X.x.x.x.X.x."); ) :
  p == 5  ? ( pc_seq(3, 0, 10, 5); shk_set(5500, 4, 110, 4, 4, 500, 5, 7, 6); pc_pat(0, "................"); pc_pat(1, "X...X...X...X..."); ) :
  p == 6  ? ( pc_seq(3, 10, 20, 6); shk_set(6000, 3, 90, 4, 4, 220, 6, 4, 6); pc_pat(0, "x.x.x.x.x.x.x.x."); pc_pat(1, "x.xxX.xxx.xxX.xx"); ) :
  p == 7  ? ( pc_seq(3, 33, 20, 6); shk_set(5200, 4, 120, 4, 5, 250, 5, 5, 5); pc_pat(0, "XxXxXxXxXxXxXxXx"); pc_pat(1, "....X.......X..."); ) :
  p == 8  ? ( pc_seq(3, 5, 20, 6); shk_set(3000, 7, 140, 5, 5, 250, 5, 5, 5); pc_pat(0, "X.xxX.xxX.xxX.xx"); pc_pat(1, "................"); ) :
  p == 9  ? ( pc_seq(3, 0, 15, 6); shk_set(5800, 3, 100, 4, 4, 300, 5, 5, 5); pc_pat(0, "XxxXxxXxxXxx"); pc_pat(1, "X...X...X...X..."); ) :
  p == 10 ? ( pc_seq(3, 10, 15, 4); shk_set(5000, 4, 130, 4, 3, 250, 5, 5, 5); pc_pat(0, "XxxxXxxxXxxxXxxx"); pc_pat(1, "................"); ) :
  p == 11 ? ( pc_seq(3, 15, 20, 6); shk_set(5600, 4, 110, 4, 5, 450, 5, 6, 6); pc_pat(0, "x.x.x.x.x.x.x.x."); pc_pat(1, "........X......."); ) :
  p == 12 ? ( pc_seq(3, 18, 25, 7); shk_set(6200, 3, 100, 4, 5, 260, 6, 5, 7); pc_pat(0, "XxxXxxXxXxxXxxXxXxxXxxXxXxxXxXxx"); pc_pat(1, "x...X..x.x..X...x...X..x"); );
  p == 13 && !pc_po ? ( slider5 = 0; slider6 = 0; slider7 = 50; slider8 = 0; rv_reset(); );
  !pc_po ? ( i = 1; loop(23, ui_auto(i); i += 1; ); pr_cur = p == 13 ? 1 : p; );
);
""" + INIT_TAIL_COMMON
PANEL = r"""
kr_sect(22, pv_y, 610, 190, "SHAKER");
sprintf(#pa, "%.1f kHz", slider15 / 1000); pv_k(72, pv_ky, 15, 1500, 9000, 5500, 1, "TONE", #pa);
sprintf(#pb, "%.1f", slider16); pv_k(152, pv_ky, 16, 0, 10, 4, 0, "BEADS", #pb);
sprintf(#pc, "%d ms", floor(slider17 + 0.5)); pv_k(232, pv_ky, 17, 30, 400, 110, 1, "STROKE", #pc);
sprintf(#pd, "%.1f", slider18); pv_k(312, pv_ky, 18, 0, 10, 4, 0, "RESO", #pd);
sprintf(#pe, "%.1f", slider19); pv_k(392, pv_ky, 19, 0, 10, 4, 0, "PUSH/PULL", #pe);
sprintf(#pf, "%+.1f dB", slider10); pv_k(482, pv_ky, 10, -24, 6, 0, 0, "LEVEL", #pf);
sprintf(#pg, "%+d", floor(slider11 + 0.5)); pv_k(562, pv_ky, 11, -100, 100, -20, 0, "PAN", #pg);
gfx_setfont(10); ui_col(KRI2); kr_ctxt(232, pv_y + 172, "GRAINS OF BEADS IN A RESONANT SHELL - PUSH AND PULL STROKES");
kr_sect(638, pv_y, 420, 190, "TAMBOURINE");
sprintf(#ph, "%d ms", floor(slider20 + 0.5)); pv_k(686, pv_ky, 20, 40, 800, 250, 1, "RING", #ph);
sprintf(#pi, "%.1f", slider21); pv_k(756, pv_ky, 21, 0, 10, 5, 0, "BRIGHT", #pi);
sprintf(#pj, "%.1f", slider22); pv_k(826, pv_ky, 22, 0, 10, 5, 0, "HIT", #pj);
sprintf(#pk, "%.1f", slider23); pv_k(896, pv_ky, 23, 0, 10, 5, 0, "RATTLE", #pk);
sprintf(#pl, "%+.1f dB", slider13); pv_k(966, pv_ky, 13, -24, 6, 0, 0, "LEVEL", #pl);
sprintf(#pm, "%+d", floor(slider14 + 0.5)); pv_k(1028, pv_ky, 14, -100, 100, 25, 0, "PAN", #pm);
gfx_setfont(10); ui_col(KRI2); kr_ctxt(848, pv_y + 172, "A FRAME HIT RINGS FIVE METAL JINGLES");
"""
build(os.path.dirname(os.path.abspath(__file__)) + '/../gfx-g-shk34.jsfx', HDR, sl, INS, SETS, gfx("SHK34","SHAKERS AND","TAMBOURINE","0xD8C08A","0xF2E8D2",["SHAKER","TAMBOURINE"],PANEL))
