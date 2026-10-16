# shared parts of SHK34 / BEL34 / CLV34
import os; S=os.environ.get('GFX_KIT_DIR', os.path.dirname(os.path.abspath(__file__)) + '/')
KIT=open(S+'ch34_kit2.txt').read()

def sliders_reverb():
    return """slider40:0<0,3,1{Off,Room,Spring,Plate}>-Reverb
slider41:5<0,10,0.1>-Reverb decay
slider42:5<0,10,0.1>-Reverb tone
slider43:25<0,100,1>-Reverb amount (%)
"""

def sliders_common(rate=3):
    return "slider1:" + str(rate) + """<0,5,1{1/4,1/8,1/8T,1/16,1/16T,1/32}>-Rate
slider2:0<0,75,1>-Swing (%)
slider3:15<0,100,1>-Humanize (%)
slider4:5<0,10,0.1>-Accent
slider5:0<0,1,1{Off,On}>-Free run (plays when stopped)
slider6:0<-24,6,0.1>-Master (dB)
slider7:50<0,100,1>-Drift (%)
slider8:0<0,1,1{VFD,Matrix}>-Look
"""

def sliders_lanes(lanes):
    out=[]; i=9
    for ln in lanes:
        nm,pan=ln[0],ln[1]; n=ln[2] if len(ln)>2 else 16
        out.append(f"slider{i}:{n}<1,32,1>-{nm} length (steps)"); out.append(f"slider{i+1}:0<-24,6,0.1>-{nm} level (dB)"); out.append(f"slider{i+2}:{pan}<-100,100,1>-{nm} pan")
        i+=3
    return "\n".join(out)+"\n", i

INIT_A = r"""
@init
ext_noinit = 1;
clp_aa = 1; clp_pf_on = 0; clp_kt_on = 0;
function pc_tn(x) ( abs(x) < 0.000000000001 ? 0 : x; );
function pc_tc(ms) ( 1 - exp(-1 / (max(ms, 0.002) * 0.001 * srate)); );
function pc_kd(ms) ( exp(-1 / (max(ms, 0.002) * 0.001 * srate)); );          // a per-sample decay factor (time constant, ms)

// ---------- memory ----------
STP = 5000;                                           // the steps: lane x 32 + step (0 off, 1 hit, 2 accent)
EX = 4000; OUT = 4010; LTR = 4020; CUR = 4030;        // per lane: excitation, output, trigger flash, playing step
MQ = 4100;                                            // the MIDI queue: offset, lane, velocity, mute
MD = 1000;                                            // the modal resonators: 8 values each
pc_nm = 0;

// ---------- the modal resonators: two-pole, an impulse of 1 rings at amplitude 1 ----------
function md_set(m, ln, f, tau, w) local(o, ww, r) (
  o = MD + m * 8; ww = 2 * $pi * min(max(f, 20), 0.45 * srate) / srate; r = exp(-1 / (max(tau, 0.0005) * srate));
  o[0] = 2 * r * cos(ww); o[1] = -r * r; o[2] = sin(ww); o[5] = w; o[6] = ln;
);
// the same, normalised for noise excitation (unity power gain, whatever the ring time)
function md_setn(m, ln, f, tau, w) local(o, ww, r) (
  o = MD + m * 8; ww = 2 * $pi * min(max(f, 20), 0.45 * srate) / srate; r = exp(-1 / (max(tau, 0.0005) * srate));
  o[0] = 2 * r * cos(ww); o[1] = -r * r; o[2] = sin(ww) * 2 * sqrt(1 - r); o[5] = w; o[6] = ln;
);
function md_run() local(o, y) (
  o = MD;
  loop(pc_nm, y = o[0] * o[3] + o[1] * o[4] + o[2] * EX[o[6]]; o[4] = o[3]; o[3] = y; OUT[o[6]] += y * o[5]; o += 8; );
);
function md_tidy() local(o) ( o = MD; loop(pc_nm, o[3] = pc_tn(o[3]); o[4] = pc_tn(o[4]); o += 8; ); );
// ---------- a state-variable band-pass (TPT) ----------
function pc_svf(f, q) instance(a1, a2, a3) local(g, k) (
  g = tan($pi * min(max(f, 20), 0.45 * srate) / srate); k = 1 / max(q, 0.3);
  a1 = 1 / (1 + g * (g + k)); a2 = g * a1; a3 = g * a2;
);
function pc_bp(x) instance(a1, a2, a3, c1, c2) local(v1, v2, v3) (
  v3 = x - c2; v1 = a1 * c1 + a2 * v3; v2 = c2 + a2 * c1 + a3 * v3; c1 = 2 * v1 - c1; c2 = 2 * v2 - c2; v1;
);
function pc_svt() instance(c1, c2) ( c1 = pc_tn(c1); c2 = pc_tn(c2); );

"""
INIT_B = r"""

// ---------- REVERB on the mix: ROOM (early reflections and a 4-line feedback network), SPRING (two dispersive
// loops, the chirp of a real tank), PLATE (a figure-8 allpass tank). DECAY, TONE, AMOUNT (added to the dry).
// Switching type fades the wet out, clears the tank and fades the new one in - no clicks.
RV_W = 6000; RV_S = 6200; RV_B = 20000;
function rv_alloc() ( rv_n = ceil(0.25 * srate) + 8; memset(RV_B, 0, 16 * rv_n); memset(RV_W, 0, 16); memset(RV_S, 0, 160); );
function rv_rd(k, d) local(i) ( i = RV_W[k] - d; i < 0 ? i += rv_n; RV_B[k * rv_n + i]; );
function rv_wr(k, x) local(i) ( i = RV_W[k]; RV_B[k * rv_n + i] = x; i += 1; i >= rv_n ? i = 0; RV_W[k] = i; );
function rv_ap(k, x, d, g) local(v, u) ( v = rv_rd(k, d); u = x - g * v; rv_wr(k, u); v + g * u; );
function rv_p(n) ( max(floor(n * srate / 29761 + 0.5), 1); );                   // plate lengths (the tank's own rate)
function rv_ms(m) ( max(floor(m * 0.001 * srate + 0.5), 1); );
function rv_setup() local(t60, k) (
  rv_tt = floor(min(max(slider40, 0), 3) + 0.5);
  rv_dk = min(max(slider41, 0), 10) / 10; rv_tn = min(max(slider42, 0), 10) / 10;
  rv_amt = min(max(slider43, 0), 100) / 100;
  rv_t != rv_tt && rv_g < 0.0003 ? ( memset(RV_B, 0, 16 * rv_n); memset(RV_W, 0, 16); memset(RV_S, 0, 160);
    rv_bw = rv_zl = rv_zr = rv_l0 = rv_l1 = rv_h0 = rv_h1 = 0; rv_t = rv_tt; );
  rv_gt = rv_t == rv_tt && rv_t > 0 ? rv_amt : 0;
  rv_t == 1 ? (                                                                  // ROOM
    t60 = 0.3 * 6 ^ rv_dk;
    RV_S[20] = rv_ms(29.7); RV_S[21] = rv_ms(37.1); RV_S[22] = rv_ms(41.3); RV_S[23] = rv_ms(47.9);
    k = 0; loop(4, RV_S[24 + k] = 10 ^ (-3 * RV_S[20 + k] / srate / t60); k += 1; );
    rv_dc = 1 - exp(-2 * $pi * 1500 * 8 ^ rv_tn / srate); rv_kn = 3.2;
  ) : rv_t == 2 ? (                                                              // SPRING
    t60 = 0.8 * 4 ^ rv_dk;
    RV_S[20] = rv_ms(37.3); RV_S[21] = rv_ms(43.9);
    RV_S[24] = min(10 ^ (-3 * (RV_S[20] / srate + 0.004) / t60), 0.97); RV_S[25] = min(10 ^ (-3 * (RV_S[21] / srate + 0.004) / t60), 0.97);
    rv_dc = 1 - exp(-2 * $pi * 2000 * 3 ^ rv_tn / srate); rv_hc = 1 - exp(-2 * $pi * 140 / srate); rv_a = -0.62; rv_kn = 0.9;
  ) : rv_t == 3 ? (                                                              // PLATE
    t60 = 0.6 * 8 ^ rv_dk;
    rv_dec = 10 ^ (-1.5 * ((672 + 4453 + 1800 + 3720) / 29761) / t60);
    rv_dc = 1 - exp(-2 * $pi * 1500 * 8 ^ rv_tn / srate); rv_bc = 1 - exp(-2 * $pi * (3000 + 9000 * rv_tn) / srate); rv_kn = 0.75;
  );
  rv_kg = 1 - exp(-1 / (0.01 * srate));
  rv_bw = pc_tn(rv_bw); rv_zl = pc_tn(rv_zl); rv_zr = pc_tn(rv_zr); rv_l0 = pc_tn(rv_l0); rv_l1 = pc_tn(rv_l1); rv_h0 = pc_tn(rv_h0); rv_h1 = pc_tn(rv_h1);
  k = 0; loop(4, RV_S[k] = pc_tn(RV_S[k]); k += 1; );
);
function rv_run(l, r) local(x, a1, a2, a3, a4, h, dl, dr, u, v, w, fl, fr, y, o, i, s) (
  rv_wl = rv_wr_ = 0;
  rv_t == 1 ? (                                                                  // ROOM
    x = (l + r) * 0.5; rv_wr(0, x);
    rv_wl = 0.42 * rv_rd(0, rv_ms(3.1)) + 0.33 * rv_rd(0, rv_ms(7.9)) + 0.26 * rv_rd(0, rv_ms(13.7)) + 0.2 * rv_rd(0, rv_ms(19.9));
    rv_wr_ = 0.42 * rv_rd(0, rv_ms(5.3)) + 0.33 * rv_rd(0, rv_ms(11.2)) + 0.26 * rv_rd(0, rv_ms(17.3)) + 0.2 * rv_rd(0, rv_ms(23.6));
    a1 = rv_rd(1, RV_S[20]); a2 = rv_rd(2, RV_S[21]); a3 = rv_rd(3, RV_S[22]); a4 = rv_rd(4, RV_S[23]);
    RV_S[0] += rv_dc * (a1 - RV_S[0]); a1 = RV_S[0] * RV_S[24];
    RV_S[1] += rv_dc * (a2 - RV_S[1]); a2 = RV_S[1] * RV_S[25];
    RV_S[2] += rv_dc * (a3 - RV_S[2]); a3 = RV_S[2] * RV_S[26];
    RV_S[3] += rv_dc * (a4 - RV_S[3]); a4 = RV_S[3] * RV_S[27];
    h = 0.5 * (a1 + a2 + a3 + a4);
    dl = rv_ap(5, l, rv_ms(4.7), 0.6); dr = rv_ap(6, r, rv_ms(6.1), 0.6);
    rv_wr(1, a1 - h + 0.5 * dl); rv_wr(2, a2 - h + 0.5 * dr); rv_wr(3, a3 - h + 0.5 * dl); rv_wr(4, a4 - h + 0.5 * dr);
    rv_wl = 0.6 * rv_wl + 0.7 * (a1 - a3); rv_wr_ = 0.6 * rv_wr_ + 0.7 * (a2 - a4);
  ) : rv_t == 2 ? (                                                              // SPRING: two tanks
    s = 0;
    loop(2,
      y = rv_rd(s, RV_S[20 + s]);
      o = RV_S + 32 + s * 64; i = 0;
      loop(48, v = rv_a * y + o[i]; o[i] = y - rv_a * v; y = v; i += 1; );     // the dispersion: the chirp
      s == 0 ? ( rv_l0 += rv_dc * (y - rv_l0); rv_h0 += rv_hc * (rv_l0 - rv_h0); y = rv_l0 - rv_h0; rv_wl = y;
                 rv_wr(0, 0.75 * l + 0.25 * r + y * RV_S[24]); )
             : ( rv_l1 += rv_dc * (y - rv_l1); rv_h1 += rv_hc * (rv_l1 - rv_h1); y = rv_l1 - rv_h1; rv_wr_ = y;
                 rv_wr(1, 0.75 * r + 0.25 * l + y * RV_S[25]); );
      s += 1;
    );
  ) : rv_t == 3 ? (                                                              // PLATE
    x = (l + r) * 0.5; rv_bw += rv_bc * (x - rv_bw);
    x = rv_ap(1, rv_bw, rv_p(142), 0.75); x = rv_ap(2, x, rv_p(107), 0.75); x = rv_ap(3, x, rv_p(379), 0.625); x = rv_ap(4, x, rv_p(277), 0.625);
    fl = rv_rd(12, rv_p(3163)) * rv_dec; fr = rv_rd(8, rv_p(3720)) * rv_dec;
    u = rv_ap(5, x + fl, rv_p(672), -0.7); v = rv_rd(6, rv_p(4453)); rv_wr(6, u);
    rv_zl += rv_dc * (v - rv_zl); w = rv_ap(7, rv_zl * rv_dec, rv_p(1800), 0.5); rv_wr(8, w);
    u = rv_ap(9, x + fr, rv_p(908), -0.7); v = rv_rd(10, rv_p(4217)); rv_wr(10, u);
    rv_zr += rv_dc * (v - rv_zr); w = rv_ap(11, rv_zr * rv_dec, rv_p(2656), 0.5); rv_wr(12, w);
    rv_wl = 0.6 * (rv_rd(10, rv_p(266)) + rv_rd(10, rv_p(2974)) - rv_rd(11, rv_p(1913)) + rv_rd(12, rv_p(1996)) - rv_rd(6, rv_p(1990)) - rv_rd(7, rv_p(187)) - rv_rd(8, rv_p(1066)));
    rv_wr_ = 0.6 * (rv_rd(6, rv_p(353)) + rv_rd(6, rv_p(3627)) - rv_rd(7, rv_p(1228)) + rv_rd(8, rv_p(2673)) - rv_rd(10, rv_p(2111)) - rv_rd(11, rv_p(335)) - rv_rd(12, rv_p(121)));
  );
);

function rv_reset() local(i) ( slider40 = 0; slider41 = 5; slider42 = 5; slider43 = 25; i = 40; loop(4, ui_auto(i); i += 1; ); );

// ---------- the sequencer ----------
function pc_div(i) ( i == 0 ? 1 : i == 1 ? 0.5 : i == 2 ? 1 / 3 : i == 3 ? 0.25 : i == 4 ? 1 / 6 : 0.125; );
function pc_len(k) ( floor(min(max(slider(9 + k * 3), 1), 32) + 0.5); );
function pc_t(n) ( n * pc_sl + ((n & 1) ? pc_sw * pc_sl : 0); );                // swing: the odd steps late
function pc_hoff() ( (rand(1) * pc_hu * 0.02 + pc_poff) * tempo / 60; );         // humanize (late only) + the player's drift
function pc_hit(k, v, a) (
  v *= (1 - pc_hu * 0.3 * rand(1)) * pc_pstr;                                     // humanize and the player's strength
  a ? v *= 1 + 0.12 * pc_acc;                                                     // ACCENT: louder (and brighter, per instrument)
  LTR[k] = 1;
  ins_trig(k, min(v, 2), a);
);
function pc_fire(n) local(k, st, v) (
  k = 0;
  loop(NL,
    st = n % pc_len(k); CUR[k] = st; v = STP[k * 32 + st];
    v > 0 ? pc_hit(k, v == 2 ? 1 : 0.72, v == 2);
    k += 1;
  );
);
function pc_resync() local(n) (
  n = floor(pc_pos / pc_sl + 0.000001); pc_t(n) < pc_pos - 0.0005 ? n += 1;
  pc_nx = n; pc_tn = pc_t(n) + pc_hoff();
);
// a pattern from a string: '.' off, 'x' hit, 'X' accent; its length sets the lane's LENGTH
function pc_pat(k, s) local(i, c, n) (
  n = min(strlen(s), 32); i = 0;
  loop(32, c = i < n ? str_getchar(s, i) : 46; STP[k * 32 + i] = c == 88 ? 2 : c == 120 ? 1 : 0; i += 1; );
  !pc_po ? slider(9 + k * 3) = n;
);
function pc_seq(rate, sw, hu, ac) ( !pc_po ? ( slider1 = rate; slider2 = sw; slider3 = hu; slider4 = ac; ); );
"""

BLOCK_COMMON = r"""
@block
srate != pc_sr ? ( pc_sr = srate; ost_init(0); ins_srinit(); rv_alloc(); );
in_setup(0, 0);
ost_setup(0, 0.3, 120, 6000, -0.3, 1);                // the house output stage: CLIP
drift_macro(slider7);
pc_n = samplesblock / srate;
pc_vt = dT.drift_tick(0.05 * dm_s * pc_n); pc_vp = dP.drift_tick(0.06 * dm_s * pc_n); pc_vs = dS.drift_tick(0.06 * dm_s * pc_n);
pc_poff = 0.006 * dm_a * (0.5 + 0.5 * pc_vp);          // the player: a few ms behind or on the beat, wandering
pc_pstr = 1 + 0.08 * dm_a * pc_vs;                     // and a little harder or softer
pc_k = 0; loop(NL, TUN[pc_k] = 2 ^ (0.0045 * dm_a * pc_vt * (pc_k & 1 ? -1 : 1) * (1 + 0.3 * pc_k) / 12); pc_k += 1; );   // tuning, a hair
// the sequencer: the transport (or FREE RUN), the division, swing, humanize
pc_sl = pc_div(floor(min(max(slider1, 0), 5) + 0.5));
pc_sw = min(max(slider2, 0), 75) / 100; pc_hu = min(max(slider3, 0), 100) / 100; pc_acc = min(max(slider4, 0), 10);
pc_free = slider5 >= 0.5;
pc_play = play_state & 1;
pc_run = pc_play || pc_free;
pc_inc = tempo / (60 * srate);
pc_play ? (
  (!pc_was || !pc_wpl || abs(beat_position - pc_pos) > 0.05 || pc_sl != pc_slw || pc_sw != pc_sww) ? ( pc_pos = beat_position; pc_resync(); ) : pc_pos = beat_position;
) : pc_free ? (
  (!pc_was || pc_wpl || pc_sl != pc_slw || pc_sw != pc_sww) ? ( pc_wpl ? pc_pos = 0; pc_resync(); );
);
pc_was = pc_run; pc_wpl = pc_play; pc_slw = pc_sl; pc_sww = pc_sw;
// MIDI: notes play the lanes (General MIDI numbers); everything passes through
pc_mq = 0; pc_mi = 0;
while(
  midirecv(pc_ofs, pc_m1, pc_m2, pc_m3) ? (
    (pc_m1 & 0xF0) == 0x90 && pc_m3 > 0 && pc_mq < 60 ? (
      pc_ln = ins_note(pc_m2);
      pc_ln >= 0 ? ( MQ[pc_mq * 4] = pc_ofs; MQ[pc_mq * 4 + 1] = pc_ln; MQ[pc_mq * 4 + 2] = pc_m3 / 127; MQ[pc_mq * 4 + 3] = pc_mute; pc_mq += 1; );
    );
    midisend(pc_ofs, pc_m1, pc_m2, pc_m3);
    1;
  );
);
pc_k = 0; loop(NL, pc_lt = 10 ^ (min(max(slider(10 + pc_k * 3), -24), 6) / 20); pc_p = (min(max(slider(11 + pc_k * 3), -100), 100) / 100 + 1) * $pi / 4;
  GLT[pc_k] = pc_lt * cos(pc_p); GRT[pc_k] = pc_lt * sin(pc_p); pc_k += 1; );
pc_mst = 10 ^ (min(max(slider6, -24), 6) / 20);
ins_block();
md_tidy();
rv_setup();
pca_ol = max(pca_ol, pc_ol); pca_or = max(pca_or, pc_or); pc_ol = pc_or = 0;
"""

SAMPLE_COMMON = r"""
@sample
spl0 = spl1 = 0;
// the sequencer's clock
pc_run ? (
  pc_pos >= pc_tn ? ( pc_fire(pc_nx); pc_nx += 1; pc_tn = pc_t(pc_nx) + pc_hoff(); );
  pc_pos += pc_inc;
);
// MIDI notes due now; a lane auditioned from the panel
pc_mi < pc_mq && MQ[pc_mi * 4] <= pc_si ? ( pc_mute = MQ[pc_mi * 4 + 3]; pc_hit(MQ[pc_mi * 4 + 1], MQ[pc_mi * 4 + 2], MQ[pc_mi * 4 + 2] > 0.85); pc_mute = 0; pc_mi += 1; );
pc_mi < pc_mq && MQ[pc_mi * 4] <= pc_si ? ( pc_mute = MQ[pc_mi * 4 + 3]; pc_hit(MQ[pc_mi * 4 + 1], MQ[pc_mi * 4 + 2], MQ[pc_mi * 4 + 2] > 0.85); pc_mute = 0; pc_mi += 1; );
pc_aud > 0 ? ( pc_hit(pc_aud - 1, 0.85, 0); pc_aud = 0; );
pc_si += 1;
// the instruments
pc_k = 0; loop(NL, OUT[pc_k] = 0; pc_k += 1; );
ins_sample();
md_run();
pc_k = 0; pc_yl = pc_yr = 0;
loop(NL,
  GL[pc_k] += (GLT[pc_k] - GL[pc_k]) * 0.002; GR[pc_k] += (GRT[pc_k] - GR[pc_k]) * 0.002;
  pc_yl += OUT[pc_k] * GL[pc_k]; pc_yr += OUT[pc_k] * GR[pc_k]; pc_k += 1;
);
pc_ms += (pc_mst - pc_ms) * 0.002;
pc_yl *= pc_ms; pc_yr *= pc_ms;
rv_g += (rv_gt - rv_g) * rv_kg;
rv_t > 0 ? ( rv_run(pc_yl, pc_yr); pc_yl += rv_wl * rv_g * rv_kn; pc_yr += rv_wr_ * rv_g * rv_kn; );
pc_yl != pc_yl ? pc_yl = 0; pc_yr != pc_yr ? pc_yr = 0;
ost_out(pc_yl, pc_yr);
spl0 = max(-4, min(4, ost_l));
spl1 = max(-4, min(4, ost_r));
pc_ol = max(pc_ol, abs(spl0)); pc_or = max(pc_or, abs(spl1));
"""

def gfx(name, sub1, sub2, vfdacc, vfdink, lanenames, soundpanel):
    nl=len(lanenames)
    rowh = 52 if nl==2 else 46 if nl==3 else 28
    names_eel=" : ".join(f'k == {i} ? "{n}"' for i,n in enumerate(lanenames[:-1]))+f' : "{lanenames[-1]}"'
    return f"""
@gfx 1080 560
ui_begin(1080, 560);
// =====================================================================
// GUI - in the 34 series manner (KRT81): the instruments' panels above, the step sequencer below (a lane per
// instrument, each with its own LENGTH: click a step for a hit, again for an accent, again to clear; click a lane's
// name to hear it). Two looks: VFD (charcoal and the instrument's colour) and MATRIX (battleship grey and cream).
// Design space 1080 x 560. Knobs: drag (SHIFT = fine), wheel, double-click = default; the value shows while touched.
// =====================================================================
pv_mx = slider8 >= 0.5;
!pv_mx ? (
  KRP = 0x2E2F31; KRF = 0x202123; KRI = {vfdink}; KRA = {vfdacc}; KRW = 0x121314; KRM = 0x55575A;
  KRC = {vfdacc}; KRPT = 0x1E1408; KRCN = {vfdacc}; KRGH = 0x2E2B27; KRAMB = 0xFFD24A; KRRED = 0xFF3B1F; KRKT = 0x1E1408;
) : (
  KRP = 0x222528; KRF = ui_mix(0x222528, 0x000000, 0.25); KRI = 0xC7BEB3; KRA = 0xF3E5C0; KRW = ui_mix(0x222528, 0x000000, 0.45);
  KRM = 0x4A4E4A; KRC = 0xF3E5C0; KRPT = 0x17191B; KRCN = 0x1E5631; KRGH = 0x2C302E; KRAMB = 0xD4A373; KRRED = 0xBC3908; KRKT = 0x17191B;
);
KRH = ui_mix(KRP, 0x000000, 0.35); KRI2 = ui_mix(KRI, KRF, 0.35);
""" + KIT + f"""
function kr_tog(idx) ( slider(idx) = slider(idx) >= 0.5 ? 0 : 1; ui_auto(idx); );
function pv_lname(k) ( {names_eel}; );
// a knob of the instruments' panels: the name above, the value below
function pv_k(cx, cy, idx, lo, hi, def, lg, name, val) local(a) (
  krv_lg = lg; a = kr_small(cx, cy, 16, idx, lo, hi, def, 11, "", val); krv_lg = 0;
  gfx_setfont(11); ui_col(a ? KRA : KRI); kr_ctxt(cx, cy - 30, name);
  gfx_setfont(10); ui_col(a ? KRA : KRI2); kr_ctxt(cx, cy + 29, val);
);

// =====================================================================
// Faceplate and header
// =====================================================================
ui_col(ui_mix(KRP, 0x000000, 0.35)); gfx_rect(0, 0, gfx_w, gfx_h);
ui_cola(0xFFFFFF, 0.08); kr_r(0, 0, 1080, 1.5); kr_r(0, 0, 1.5, 560);
ui_cola(0x000000, 0.35); kr_r(0, 558.5, 1080, 1.5); kr_r(1078.5, 0, 1.5, 560);
ui_col(KRP); kr_r(12, 12, 1056, 536);
ui_cola(0x000000, 0.30); kr_r(12, 12, 1056, 1.5); kr_r(12, 12, 1.5, 536);
ui_cola(0xFFFFFF, 0.07); kr_r(12, 546.5, 1056, 1.5); kr_r(1066.5, 12, 1.5, 536);
ui_col(KRH); kr_r(13.5, 13.5, 1053, 50.5);
ui_col(KRA); kr_r(13.5, 64, 1053, 2);
ui_col(KRA); gfx_circle(45 * sc, 39 * sc, 16 * sc, 1, 1);
gfx_setfont(4); ui_col(KRKT); ui_text(45 * sc, 33.5 * sc, "GFX");
gfx_setfont(6); ui_col(KRI); kr_txt(72, 24, "{name}"); gfx_measurestr("{name}", pv_tw, pv_th);
pv_tx = 72 + pv_tw / sc + 14;
gfx_setfont(11); ui_col(KRI2); kr_txt(pv_tx, 25, "{sub1}"); kr_txt(pv_tx, 40, "{sub2}");
pk_pextra = "Reset all to defaults";
k_ = pk_preset(340 * sc, 22 * sc, 290 * sc, 34 * sc, pr_cur, #pc_pm);
k_ > 0 ? load_preset(k_);
kr_key(800, 25, 56, 28, "VFD", pv_mx == 0) ? ( slider8 = 0; ui_auto(8); );
kr_key(860, 25, 66, 28, "MATRIX", pv_mx == 1) ? ( slider8 = 1; ui_auto(8); );
ui_size_picker(1000 * sc, 30 * sc);

// =====================================================================
// The instruments
// =====================================================================
pv_y = 72; pv_ky = pv_y + 104;
{soundpanel}

// =====================================================================
// The sequencer
// =====================================================================
kr_sect(22, 268, 1036, 192, "SEQUENCER");
gfx_setfont(10); ui_col(play_state & 1 || slider5 >= 0.5 ? KRA : KRI2); kr_txt(31, 292, play_state & 1 ? "PLAYING" : slider5 >= 0.5 ? "FREE RUN" : "STOPPED");
pv_i = 0;
loop(6,
  kr_key(132 + pv_i * 42, 274, 40, 22, pv_i == 0 ? "1/4" : pv_i == 1 ? "1/8" : pv_i == 2 ? "1/8T" : pv_i == 3 ? "1/16" : pv_i == 4 ? "1/16T" : "1/32",
    floor(slider1 + 0.5) == pv_i) ? ( slider1 = pv_i; ui_auto(1); );
  pv_i += 1;
);
function pv_sk(x, idx, lo, hi, def, name, val) local(a) (
  a = kr_small(x, 285, 11, idx, lo, hi, def, 11, "", val);
  gfx_setfont(11); ui_col(a ? KRA : KRI2); kr_rtxt(x - 22, 286, a ? val : name);   // (the name turns into its value while touched)
);
sprintf(#pvs1, "%d%%", floor(slider2 + 0.5)); pv_sk(458, 2, 0, 75, 0, "SWING", #pvs1);
sprintf(#pvs2, "%d%%", floor(slider3 + 0.5)); pv_sk(570, 3, 0, 100, 15, "HUMAN", #pvs2);
sprintf(#pvs3, "%.1f", slider4); pv_sk(684, 4, 0, 10, 5, "ACCENT", #pvs3);
kr_key(712, 274, 56, 22, "FREE", slider5 >= 0.5) ? kr_tog(5);
sprintf(#pvs4, "%+.1f", slider6); pv_sk(870, 6, -24, 6, 0, "MASTER", #pvs4);
sprintf(#pvs5, "%d%%", floor(slider7 + 0.5)); pv_sk(1000, 7, 0, 100, 50, "DRIFT", #pvs5);
// the lanes
pv_rh = {rowh}; pv_y0 = 306;
pv_k = 0;
loop(NL,
  pv_yy = pv_y0 + pv_k * pv_rh; pv_h = pv_rh - 6;
  LTF[pv_k] = max(LTF[pv_k] * 0.82, LTR[pv_k]); LTR[pv_k] = 0;
  kr_key(28, pv_yy, 96, pv_h, pv_lname(pv_k), LTF[pv_k] > 0.25) ? pc_aud = pv_k + 1;
  pv_len = pc_len(pv_k);
  pv_len > 1 ? ( kr_key(128, pv_yy + (pv_h - 20) * 0.5, 18, 20, "◄", 0) ? ( slider(9 + pv_k * 3) = pv_len - 1; ui_auto(9 + pv_k * 3); ); ) : kr_dim(128, pv_yy + (pv_h - 20) * 0.5, 18, 20, "◄");
  sprintf(#pvl, "%d", pv_len); gfx_setfont(11); ui_col(KRA); kr_ctxt(162, pv_yy + pv_h * 0.5, #pvl);
  pv_len < 32 ? ( kr_key(178, pv_yy + (pv_h - 20) * 0.5, 18, 20, "►", 0) ? ( slider(9 + pv_k * 3) = pv_len + 1; ui_auto(9 + pv_k * 3); ); ) : kr_dim(178, pv_yy + (pv_h - 20) * 0.5, 18, 20, "►");
  pv_s = 0;
  loop(32,
    pv_x = 202 + pv_s * 26 + floor(pv_s / 4) * 0;
    pv_v = STP[pv_k * 32 + pv_s]; pv_in = pv_s < pv_len;
    pv_hov = kr_hov(pv_x, pv_yy, 23, pv_h);
    pv_hov && pressed && drag_id == 0 ? ( drag_id = -1; STP[pv_k * 32 + pv_s] = (pv_v + 1) % 3; pv_v = STP[pv_k * 32 + pv_s]; );
    ui_col(0x050505); kr_r(pv_x, pv_yy, 23, pv_h);
    pv_v == 0 ? ui_col(pv_in ? ((pv_s & 3) == 0 ? ui_mix(KRGH, 0xFFFFFF, 0.06) : KRGH) : ui_mix(KRF, 0x000000, 0.3)) :
                ui_col(pv_v == 2 ? KRA : ui_mix(KRA, KRF, pv_in ? 0.45 : 0.75));
    kr_r(pv_x + 1, pv_yy + 1, 21, pv_h - 2);
    pv_v == 2 ? ( ui_cola(0xFFFFFF, 0.35); kr_r(pv_x + 1, pv_yy + 1, 21, 2); );
    pv_in && pv_s == CUR[pv_k] && (play_state & 1 || slider5 >= 0.5) ? ( ui_cola(0xFFFFFF, 0.5); kr_r(pv_x, pv_yy + pv_h - 3, 23, 3); );
    pv_s += 1;
  );
  pv_k += 1;
);
gfx_setfont(10); ui_col(KRI2); kr_txt(202, 448, "CLICK: HIT  -  AGAIN: ACCENT  -  AGAIN: OFF.   EACH LANE ITS OWN LENGTH.   MIDI NOTES PLAY THE LANES TOO.");

// the reverb
kr_sect(22, 468, 1036, 70, "REVERB");
pv_i = 0;
loop(4,
  kr_key(132 + pv_i * 64, 492, 60, 24, pv_i == 0 ? "OFF" : pv_i == 1 ? "ROOM" : pv_i == 2 ? "SPRING" : "PLATE",
    floor(slider40 + 0.5) == pv_i) ? ( slider40 = pv_i; ui_auto(40); );
  pv_i += 1;
);
function pv_rk(x, idx, lo, hi, def, name, val) local(a) (
  a = kr_small(x, 504, 11, idx, lo, hi, def, 11, "", val);
  gfx_setfont(11); ui_col(a ? KRA : KRI2); kr_rtxt(x - 22, 505, a ? val : name);
);
pv_rt = floor(slider40 + 0.5);
sprintf(#pvr1, "%.1f s", pv_rt == 2 ? 0.8 * 4 ^ (slider41 / 10) : pv_rt == 3 ? 0.6 * 8 ^ (slider41 / 10) : 0.3 * 6 ^ (slider41 / 10));
pv_rk(560, 41, 0, 10, 5, "DECAY", #pvr1);
sprintf(#pvr2, "%.1f", slider42); pv_rk(720, 42, 0, 10, 5, "TONE", #pvr2);
sprintf(#pvr3, "%d%%", floor(slider43 + 0.5)); pv_rk(900, 43, 0, 100, 25, "AMOUNT", #pvr3);

pk_end();
ui_end();
"""

def build(fn, header, sliders, ins_code, sets_code, gfxtxt, ser_extra=""):
    txt = header + sliders + sliders_reverb() + """
in_pin:left input
in_pin:right input
out_pin:left output
out_pin:right output

import gfx-input.jsfx-inc
import gfx-output.jsfx-inc
import gfx-drift.jsfx-inc
import gfx-ui.jsfx-inc
import gfx-panel.jsfx-inc
import gfx-dyn.jsfx-inc
import gfx-clip.jsfx-inc
""" + INIT_A + ins_code + INIT_B + sets_code + """
@serialize
file_var(0, ui_sz);
file_var(0, pr_cur);
file_mem(0, STP, 160);
""" + ser_extra + BLOCK_COMMON + SAMPLE_COMMON.replace("pc_si += 1;","pc_si += 1;") + gfxtxt
    # reset the sample index each block
    txt = txt.replace("pc_mq = 0; pc_mi = 0;","pc_mq = 0; pc_mi = 0; pc_si = 0;")
    open(fn,'w').write(txt)

INIT_TAIL_COMMON = r"""
// ---------- state ----------
TUN = 4040; GL = 4050; GR = 4060; GLT = 4070; GRT = 4080; LTF = 4090;
pc_sr = srate; ost_init(0); ins_srinit(); rv_alloc();
in_init();
dT.drift_init(0.8 + rand(0.4)); dP.drift_init(0.8 + rand(0.4)); dS.drift_init(0.8 + rand(0.4));
drift_macro(50);
pc_k = 0; loop(NL, TUN[pc_k] = 1; pc_k += 1; );
pc_pstr = 1;
ui_thm = 5; ui_hw = 1;                                // house keycaps for the preset bar and the size picker
!ui_dflt ? ( ui_sz = 0; pr_cur = 1; pc_po = 1; load_preset(1); pc_po = 0; );   // new instances: Medium, Init's patterns
ui_dflt = 1;
"""
