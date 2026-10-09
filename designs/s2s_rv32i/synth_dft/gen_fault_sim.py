#!/usr/bin/env python3
"""
Generate a compiled C fault simulator from Yosys JSON netlist.
Uses bit-parallel simulation (64 patterns per batch) with fault dropping.
Adapted from PicoRV32 P1.3 for s2s_rv32i with additional cell types.
"""
import json, sys
from collections import defaultdict

PREFIX = "sky130_fd_sc_hd__"
DFF_TYPES = {'dfxtp_1', 'dfxtp_2', 'dfxtp_4', 'sdfxtp_1', 'sdfxtp_2', 'sdfxtp_4'}

def strip(t):
    if t.startswith('\\'):
        t = t[1:]
    if t.startswith(PREFIX):
        t = t[len(PREFIX):]
    return t

GATE_EXPRS = {
    'inv_1': ('Y', '~{A}'), 'inv_2': ('Y', '~{A}'),
    'buf_1': ('X', '{A}'), 'buf_2': ('X', '{A}'),
    'clkinv_1': ('Y', '~{A}'), 'clkinv_2': ('Y', '~{A}'),
    'clkbuf_1': ('X', '{A}'), 'clkbuf_2': ('X', '{A}'), 'clkbuf_4': ('X', '{A}'),
    'and2_0': ('X', '{A}&{B}'),
    'and2_1': ('X', '{A}&{B}'), 'and2_2': ('X', '{A}&{B}'),
    'and3_1': ('X', '{A}&{B}&{C}'), 'and4_1': ('X', '{A}&{B}&{C}&{D}'),
    'and3b_1': ('X', '(~{A_N})&{B}&{C}'), 'and4b_1': ('X', '(~{A_N})&{B}&{C}&{D}'),
    'or2_1': ('X', '{A}|{B}'), 'or2_2': ('X', '{A}|{B}'),
    'or3_1': ('X', '{A}|{B}|{C}'), 'or4_1': ('X', '{A}|{B}|{C}|{D}'),
    'or3b_1': ('X', '{A}|{B}|(~{C_N})'), 'or4b_1': ('X', '{A}|{B}|{C}|(~{D_N})'),
    'nand2_1': ('Y', '~({A}&{B})'), 'nand2b_1': ('Y', '~((~{A_N})&{B})'),
    'nand3_1': ('Y', '~({A}&{B}&{C})'), 'nand3b_1': ('Y', '~((~{A_N})&{B}&{C})'),
    'nand4_1': ('Y', '~({A}&{B}&{C}&{D})'), 'nand4b_1': ('Y', '~((~{A_N})&{B}&{C}&{D})'),
    'nand4bb_1': ('Y', '~((~{A_N})&(~{B_N})&{C}&{D})'),
    'nor2_1': ('Y', '~({A}|{B})'), 'nor2b_1': ('Y', '~({A}|(~{B_N}))'),
    'nor3_1': ('Y', '~({A}|{B}|{C})'), 'nor3b_1': ('Y', '~({A}|{B}|(~{C_N}))'),
    'nor4_1': ('Y', '~({A}|{B}|{C}|{D})'), 'nor4b_1': ('Y', '~({A}|{B}|{C}|(~{D_N}))'),
    'nor4bb_1': ('Y', '~({A}|{B}|(~{C_N})|(~{D_N}))'),
    'xor2_1': ('X', '{A}^{B}'), 'xnor2_1': ('Y', '~({A}^{B})'),
    'mux2_1': ('X', '({S}&{A1})|((~{S})&{A0})'),
    'mux2i_1': ('Y', '~(({S}&{A1})|((~{S})&{A0}))'),
    'mux4_2': ('X', '({S1}&{S0}&{A3})|({S1}&(~{S0})&{A2})|((~{S1})&{S0}&{A1})|((~{S1})&(~{S0})&{A0})'),
    # AOI
    'a21oi_1': ('Y', '~(({A1}&{A2})|{B1})'),
    'a21o_1': ('X', '({A1}&{A2})|{B1}'),
    'a21boi_0': ('Y', '~(({A1}&{A2})|(~{B1_N}))'),
    'a22o_1': ('X', '({A1}&{A2})|({B1}&{B2})'),
    'a22oi_1': ('Y', '~(({A1}&{A2})|({B1}&{B2}))'),
    'a211o_1': ('X', '({A1}&{A2})|{B1}|{C1}'),
    'a211oi_1': ('Y', '~(({A1}&{A2})|{B1}|{C1})'),
    'a221o_1': ('X', '({A1}&{A2})|({B1}&{B2})|{C1}'),
    'a221oi_1': ('Y', '~(({A1}&{A2})|({B1}&{B2})|{C1})'),
    'a222oi_1': ('Y', '~(({A1}&{A2})|({B1}&{B2})|({C1}&{C2}))'),
    'a311o_1': ('X', '({A1}&{A2}&{A3})|{B1}|{C1}'),
    'a311oi_1': ('Y', '~(({A1}&{A2}&{A3})|{B1}|{C1})'),
    'a31o_1': ('X', '({A1}&{A2}&{A3})|{B1}'),
    'a31oi_1': ('Y', '~(({A1}&{A2}&{A3})|{B1})'),
    'a32oi_1': ('Y', '~(({A1}&{A2}&{A3})|({B1}&{B2}))'),
    'a41o_1': ('X', '({A1}&{A2}&{A3}&{A4})|{B1}'),
    'a41oi_1': ('Y', '~(({A1}&{A2}&{A3}&{A4})|{B1})'),
    'a2111o_1': ('X', '({A1}&{A2})|{B1}|{C1}|{D1}'),
    'a2111oi_0': ('Y', '~(({A1}&{A2})|{B1}|{C1}|{D1})'),
    # OAI
    'o21ai_0': ('Y', '~(({A1}|{A2})&{B1})'),
    'o21a_1': ('X', '({A1}|{A2})&{B1}'),
    'o21ba_1': ('X', '({A1}|{A2})&(~{B1_N})'),
    'o21bai_1': ('Y', '~(({A1}|{A2})&(~{B1_N}))'),
    'o22a_1': ('X', '({A1}|{A2})&({B1}|{B2})'),
    'o22ai_1': ('Y', '~(({A1}|{A2})&({B1}|{B2}))'),
    'o211a_1': ('X', '({A1}|{A2})&{B1}&{C1}'),
    'o211ai_1': ('Y', '~(({A1}|{A2})&{B1}&{C1})'),
    'o221a_1': ('X', '({A1}|{A2})&({B1}|{B2})&{C1}'),
    'o221ai_1': ('Y', '~(({A1}|{A2})&({B1}|{B2})&{C1})'),
    'o2111ai_1': ('Y', '~(({A1}|{A2})&{B1}&{C1}&{D1})'),
    'o311ai_0': ('Y', '~(({A1}|{A2}|{A3})&{B1})'),
    'o31a_1': ('X', '({A1}|{A2}|{A3})&{B1}'),
    'o31ai_1': ('Y', '~(({A1}|{A2}|{A3})&{B1})'),
    'o32ai_1': ('Y', '~(({A1}|{A2}|{A3})&({B1}|{B2}))'),
    'o41a_1': ('X', '({A1}|{A2}|{A3}|{A4})&{B1}'),
    'o41ai_1': ('Y', '~(({A1}|{A2}|{A3}|{A4})&{B1})'),
    'o2bb2ai_1': ('Y', '~(((~{A1_N})|(~{A2_N}))&({B1}|{B2}))'),
    'lpflow_inputiso1p_1': ('X', '{A}|{SLEEP}'),
    'lpflow_isobufsrc_1': ('X', '{A}&(~{SLEEP})'),
    'maj3_1': ('X', '({A}&{B})|({A}&{C})|({B}&{C})'),
}


def main():
    with open('s2s_rv32i_netlist.json') as f:
        data = json.load(f)

    top_name = None
    for name, mod in data['modules'].items():
        attrs = mod.get('attributes', {})
        if attrs.get('top', 0) == 1 or str(attrs.get('top', '0')) == '1':
            top_name = name
            break
    if not top_name:
        top_name = list(data['modules'].keys())[0]

    top = data['modules'][top_name]
    cells = top['cells']
    ports = top['ports']

    all_bits = set()
    for pinfo in ports.values():
        for b in pinfo['bits']:
            if isinstance(b, int):
                all_bits.add(b)
    for cinfo in cells.values():
        for bits in cinfo['connections'].values():
            for b in bits:
                if isinstance(b, int):
                    all_bits.add(b)

    bit_list = sorted(all_bits - {0, 1})
    bit_to_idx = {b: i + 2 for i, b in enumerate(bit_list)}
    num_nets = len(bit_list) + 2

    def idx(b):
        if isinstance(b, str):
            return 1 if b == '1' else 0
        if b == 0: return 0
        if b == 1: return 1
        return bit_to_idx.get(b, 0)

    pi_indices = []
    po_indices = []
    dff_q_indices = []
    dff_d_indices = []
    comb_cells_data = []

    for pname, pinfo in ports.items():
        if pname in ('clk', 'CLK'):
            continue
        direction = pinfo['direction']
        for b in pinfo['bits']:
            if isinstance(b, int) and b > 1:
                if direction == 'input':
                    pi_indices.append(idx(b))
                elif direction == 'output':
                    po_indices.append(idx(b))

    for cname, cinfo in cells.items():
        basename = strip(cinfo['type'])
        conns = cinfo['connections']
        port_dirs = cinfo.get('port_directions', {})

        if basename in DFF_TYPES:
            for b in conns.get('Q', []):
                if isinstance(b, int) and b > 1:
                    dff_q_indices.append(idx(b))
            for b in conns.get('D', []):
                if isinstance(b, int) and b > 1:
                    dff_d_indices.append(idx(b))
            continue

        if basename not in GATE_EXPRS:
            print(f"WARNING: Unknown cell type {basename}, skipping", file=sys.stderr)
            continue

        out_port, expr_template = GATE_EXPRS[basename]

        input_map = {}
        out_idx = None
        for pname_c, bits in conns.items():
            direction = port_dirs.get(pname_c, 'input')
            if direction == 'output':
                b = bits[0] if bits else None
                if b is not None and not isinstance(b, str) and b > 1:
                    out_idx = idx(b)
            else:
                if bits:
                    input_map[pname_c] = idx(bits[0])

        if out_idx is None:
            continue

        expr = expr_template
        for port_name, net_idx in input_map.items():
            expr = expr.replace('{' + port_name + '}', f'n[{net_idx}]')

        comb_cells_data.append((out_idx, expr, set(input_map.values())))

    # Topological sort
    available = set([0, 1])
    available.update(pi_indices)
    available.update(dff_q_indices)

    ordered = []
    remaining = list(range(len(comb_cells_data)))
    changed = True
    while changed and remaining:
        changed = False
        new_remaining = []
        for i in remaining:
            out_idx, expr, deps = comb_cells_data[i]
            if deps.issubset(available):
                ordered.append(i)
                available.add(out_idx)
                changed = True
            else:
                new_remaining.append(i)
        remaining = new_remaining

    if remaining:
        print(f"WARNING: {len(remaining)} cells not levelized, adding anyway", file=sys.stderr)
        ordered.extend(remaining)

    fault_sites = set()
    for i in ordered:
        out_idx = comb_cells_data[i][0]
        fault_sites.add(out_idx)
    fault_sites.update(pi_indices)
    fault_sites.update(dff_q_indices)
    fault_sites_list = sorted(fault_sites)

    obs_indices = sorted(set(po_indices + dff_d_indices))

    print(f"Nets: {num_nets}, Comb cells: {len(ordered)}, DFFs: {len(dff_q_indices)}")
    print(f"PI: {len(pi_indices)}, PO: {len(po_indices)}")
    print(f"Fault sites: {len(fault_sites_list)}, Total faults: {len(fault_sites_list)*2}")
    print(f"Observable outputs: {len(obs_indices)}")

    with open('fault_sim.c', 'w') as f:
        f.write("""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

typedef uint64_t u64;
""")
        f.write(f"#define NUM_NETS {num_nets}\n")
        f.write(f"#define NUM_FAULTS {len(fault_sites_list)*2}\n")
        f.write(f"#define NUM_OBS {len(obs_indices)}\n")
        f.write(f"#define NUM_PI {len(pi_indices)}\n")
        f.write(f"#define NUM_DFF {len(dff_q_indices)}\n\n")

        f.write("static u64 n[NUM_NETS];\n")
        f.write("static u64 good[NUM_NETS];\n\n")

        f.write(f"static int pi_idx[{len(pi_indices)}] = {{")
        f.write(','.join(str(x) for x in pi_indices))
        f.write("};\n")

        f.write(f"static int dff_idx[{len(dff_q_indices)}] = {{")
        f.write(','.join(str(x) for x in dff_q_indices))
        f.write("};\n")

        f.write(f"static int obs_idx[{len(obs_indices)}] = {{")
        f.write(','.join(str(x) for x in obs_indices))
        f.write("};\n")

        f.write(f"static int fault_net[NUM_FAULTS] = {{")
        faults = []
        for s in fault_sites_list:
            faults.append(str(s))
            faults.append(str(s))
        f.write(','.join(faults))
        f.write("};\n")

        f.write(f"static int fault_val[NUM_FAULTS] = {{")
        fvals = []
        for s in fault_sites_list:
            fvals.append('0')
            fvals.append('1')
        f.write(','.join(fvals))
        f.write("};\n\n")

        f.write("static void simulate(void) {\n")
        f.write("    n[0] = 0ULL;\n")
        f.write("    n[1] = ~0ULL;\n")
        for i in ordered:
            out_idx, expr, _ = comb_cells_data[i]
            f.write(f"    n[{out_idx}] = {expr};\n")
        f.write("}\n\n")

        f.write("static void simulate_fault(int fnet, u64 stuck) {\n")
        f.write("    n[0] = 0ULL;\n")
        f.write("    n[1] = ~0ULL;\n")
        for i in ordered:
            out_idx, expr, _ = comb_cells_data[i]
            f.write(f"    n[{out_idx}] = {expr};\n")
            f.write(f"    if (__builtin_expect({out_idx} == fnet, 0)) n[{out_idx}] = stuck;\n")
        f.write("}\n\n")

        f.write("""static u64 rng_state = 0x123456789ABCDEF0ULL;
static u64 rng64(void) {
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 7;
    rng_state ^= rng_state << 17;
    return rng_state;
}

""")

        f.write("""int main(int argc, char **argv) {
    int num_patterns = 2048;
    if (argc > 1) num_patterns = atoi(argv[1]);

    int detected[NUM_FAULTS];
    memset(detected, 0, sizeof(detected));
    int total_detected = 0;

    int batches = (num_patterns + 63) / 64;

    clock_t t0 = clock();

    for (int batch = 0; batch < batches; batch++) {
        for (int i = 0; i < NUM_PI; i++)
            n[pi_idx[i]] = rng64();
        for (int i = 0; i < NUM_DFF; i++)
            n[dff_idx[i]] = rng64();

        simulate();
        memcpy(good, n, sizeof(n));

        for (int fi = 0; fi < NUM_FAULTS; fi++) {
            if (detected[fi]) continue;

            int fnet = fault_net[fi];
            u64 stuck = fault_val[fi] ? ~0ULL : 0ULL;

            u64 excited = good[fnet] ^ stuck;
            if (!excited) continue;

            memcpy(n, good, sizeof(n));
            n[fnet] = stuck;
            simulate_fault(fnet, stuck);

            for (int oi = 0; oi < NUM_OBS; oi++) {
                u64 diff = (n[obs_idx[oi]] ^ good[obs_idx[oi]]) & excited;
                if (diff) {
                    detected[fi] = 1;
                    total_detected++;
                    break;
                }
            }
        }

        if (batch % 4 == 3 || batch == batches - 1) {
            double elapsed = (double)(clock() - t0) / CLOCKS_PER_SEC;
            double cov = 100.0 * total_detected / NUM_FAULTS;
            fprintf(stderr, "  Batch %d/%d: %.1f%% coverage (%d/%d), %.1fs\\n",
                    batch+1, batches, cov, total_detected, NUM_FAULTS, elapsed);
        }
    }

    double elapsed = (double)(clock() - t0) / CLOCKS_PER_SEC;
    double coverage = 100.0 * total_detected / NUM_FAULTS;

    printf("\\n=== ATPG Stuck-at Fault Simulation Results ===\\n");
    printf("Design: s2s_rv32i_core\\n");
    printf("Patterns applied: %d (in %d batches of 64)\\n", batches * 64, batches);
    printf("Total stuck-at faults: %d\\n", NUM_FAULTS);
    printf("Detected faults: %d\\n", total_detected);
    printf("Undetected faults: %d\\n", NUM_FAULTS - total_detected);
    printf("Fault coverage: %.2f%%\\n", coverage);
    printf("Elapsed time: %.1fs\\n", elapsed);

    return 0;
}
""")

    print(f"Generated fault_sim.c ({len(ordered)} gate evaluations)")


if __name__ == '__main__':
    main()
