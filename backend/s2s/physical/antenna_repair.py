"""Post-detailed-route antenna repair via targeted diode insertion (P1.0A).

OpenLane 2.3.10's `repair_antennas` runs on the global-route estimate only. Detailed routing
(TritonRoute) changes wire topology — splits met1 segments, alters layer assignments — creating
antenna violations the global-route repair cannot see (lesson s2s-ant-001). This module runs AFTER
detailed routing, on the real routed ODB:

  1. check_antennas -verbose  → identify every violating net/pin/layer
  2. for each violation: place sky130_fd_sc_hd__diode_2 near the gate pin, connect to the net
  3. legalize the placed diodes (detailed_placement)
  4. incremental detailed route (TritonRoute on the changed nets)
  5. re-check antennas
  6. write the repaired ODB back to disk

The Tcl runs inside OpenROAD (same binary as the OpenLane image ships). The runner pattern is
identical to signoff.py's antenna() function: write a Tcl script, invoke `openroad -exit -no_splash`.
The ODB already contains all library cell definitions (including the diode), so no LEF reads needed.
"""
from __future__ import annotations

import re
from pathlib import Path

from s2s.physical import dfm
from s2s.tools import runner

DIODE_CELL = "sky130_fd_sc_hd__diode_2"
DIODE_PIN = "DIODE"
MAX_REPAIR_ITERATIONS = 3


def repair_tcl(odb: Path, report_before: Path, report_after: Path,
               repaired_odb: Path | None = None,
               max_iterations: int = MAX_REPAIR_ITERATIONS) -> str:
    """OpenROAD Tcl script that reads the routed ODB, finds antenna violations, inserts diodes
    at the violating gate pins, legalizes, re-routes the affected nets, and re-checks.

    The ODB already has all library cell definitions loaded (from the synthesis/floorplan stages),
    so no explicit LEF reads are needed — matching the signoff.py antenna check pattern.

    The script loops up to `max_iterations` times, stopping when check_antennas reports zero
    violations. Each iteration targets only the nets that still violate."""
    write_db = f'\nwrite_db {Path(repaired_odb).resolve()}' if repaired_odb else ""
    return f"""\
read_db {Path(odb).resolve()}

set before_rpt "{Path(report_before).resolve()}"
set after_rpt "{Path(report_after).resolve()}"

# --- initial check on the detailed-routed design ---
check_antennas -verbose -report_file $before_rpt
set viol_log [ant::antenna_violation_count]
puts "S2S_ANT_BEFORE nets=$viol_log"

# read the counts from the log output (OpenROAD prints "Found N net violations" and "Found N pin violations")
# we parse the report file instead for the pin-level detail

# check if there are any violations at all
set rpt_text [open $before_rpt r]
set rpt_content [read $rpt_text]
close $rpt_text
set has_violations [regexp {{Net:}} $rpt_content]

if {{!$has_violations}} {{
    puts "S2S_ANT_REPAIR_SKIP no violations in report"
    puts "S2S_ANT_REPAIR_DONE"
    exit
}}

set total_diodes_inserted 0
set current_rpt $before_rpt

for {{set iter 0}} {{$iter < {max_iterations}}} {{incr iter}} {{
    puts "S2S_ANT_REPAIR_ITER $iter"

    # parse the verbose report to find violating instance pins
    set f [open $current_rpt r]
    set rpt [read $f]
    close $f

    # collect violating instance pins: lines matching "Pin: inst/pin" under a "Net:" header,
    # followed by a "Required ratio: N (check)" where N > 0 and the ratio exceeds it
    set viol_pins [list]
    set cur_net ""
    set cur_pin ""
    set cur_ratio 0.0
    foreach line [split $rpt "\\n"] {{
        if {{[regexp {{^Net: (\\S+)}} $line -> n]}} {{
            set cur_net $n
            set cur_pin ""
            set cur_ratio 0.0
        }}
        if {{[regexp {{^\\s+Pin:\\s+(\\S+)}} $line -> p]}} {{
            set cur_pin $p
        }}
        if {{[regexp {{ratio:\\s+([\\d.]+)}} $line -> r]}} {{
            set cur_ratio $r
        }}
        if {{[regexp {{Required ratio:\\s+([\\d.]+)}} $line -> req]}} {{
            if {{$req > 0 && $cur_ratio > $req && $cur_pin ne ""}} {{
                if {{[string first "/" $cur_pin] >= 0}} {{
                    lappend viol_pins [list $cur_pin $cur_net]
                }}
            }}
        }}
    }}

    # deduplicate by pin
    set seen [dict create]
    set unique_pins [list]
    foreach entry $viol_pins {{
        set p [lindex $entry 0]
        if {{![dict exists $seen $p]}} {{
            dict set seen $p 1
            lappend unique_pins $entry
        }}
    }}
    set viol_pins $unique_pins
    set n_viol [llength $viol_pins]
    puts "S2S_ANT_VIOL_PINS $n_viol"

    if {{$n_viol == 0}} {{
        break
    }}

    set block [ord::get_db_block]
    set inserted 0

    foreach entry $viol_pins {{
        set vpin [lindex $entry 0]
        set net_name [lindex $entry 1]
        set parts [split $vpin "/"]
        set inst_name [lindex $parts 0]
        set pin_name [lindex $parts 1]

        # find the instance
        set inst [$block findInst $inst_name]
        if {{$inst eq "NULL"}} {{
            puts "S2S_ANT_WARN instance $inst_name not found, skipping"
            continue
        }}

        # find the ITerm (instance terminal)
        set iterm [$inst findITerm $pin_name]
        if {{$iterm eq "NULL"}} {{
            puts "S2S_ANT_WARN pin $vpin not found, skipping"
            continue
        }}

        # get pin location for diode placement
        set bbox [$iterm getBBox]
        set px [expr {{([$bbox xMin] + [$bbox xMax]) / 2}}]
        set py [expr {{([$bbox yMin] + [$bbox yMax]) / 2}}]

        # find the diode master cell
        set db [ord::get_db]
        set diode_master [lindex [$db findMaster {DIODE_CELL}] 0]
        if {{$diode_master eq "" || $diode_master eq "NULL"}} {{
            # try through the libs
            foreach lib [$db getLibs] {{
                set diode_master [$lib findMaster {DIODE_CELL}]
                if {{$diode_master ne "NULL" && $diode_master ne ""}} {{
                    break
                }}
            }}
        }}
        if {{$diode_master eq "" || $diode_master eq "NULL"}} {{
            puts "S2S_ANT_WARN diode cell {DIODE_CELL} not found in DB"
            break
        }}

        # create the diode instance name (sanitize special characters)
        set dname "S2S_ant_${{inst_name}}_${{pin_name}}_${{iter}}"
        regsub -all {{[\\[\\]/\\\\]}} $dname "_" dname

        # create the diode instance
        set diode_inst [odb::dbInst_create $block $diode_master $dname]
        if {{$diode_inst eq "NULL"}} {{
            puts "S2S_ANT_WARN could not create diode instance $dname"
            continue
        }}

        # place near the gate pin
        $diode_inst setLocation $px $py
        $diode_inst setPlacementStatus PLACED

        # connect the diode pin to the same net
        set net [$block findNet $net_name]
        if {{$net eq "NULL"}} {{
            puts "S2S_ANT_WARN net $net_name not found, skipping connection"
            continue
        }}
        set diode_iterm [$diode_inst findITerm {DIODE_PIN}]
        if {{$diode_iterm ne "NULL"}} {{
            $diode_iterm connect $net
        }}

        incr inserted
    }}

    set total_diodes_inserted [expr {{$total_diodes_inserted + $inserted}}]
    puts "S2S_ANT_INSERTED $inserted diodes (total $total_diodes_inserted)"

    if {{$inserted == 0}} {{
        puts "S2S_ANT_WARN no diodes could be inserted, stopping"
        break
    }}

    # legalize placement (moves diodes to legal sites)
    catch {{
        detailed_placement
    }} dp_result
    puts "S2S_ANT_LEGALIZE $dp_result"

    # incremental detailed route
    catch {{
        detailed_route -droute_end_iter 3
    }} dr_result
    puts "S2S_ANT_ROUTE $dr_result"

    # re-check antennas
    check_antennas -verbose -report_file $after_rpt
    set current_rpt $after_rpt

    # count remaining violations from the report
    set f [open $after_rpt r]
    set rpt [read $f]
    close $f
    set remaining [regexp -all {{^Net: }} $rpt]
    puts "S2S_ANT_AFTER_ITER$iter remaining_nets=$remaining"

    if {{$remaining == 0}} {{
        break
    }}
}}

puts "S2S_ANT_TOTAL_DIODES $total_diodes_inserted"
check_antennas -verbose -report_file $after_rpt
puts "S2S_ANT_FINAL_CHECK done"{write_db}
puts "S2S_ANT_REPAIR_DONE"
"""


_BEFORE = re.compile(r"S2S_ANT_BEFORE nets=(\d+)")
_FINAL_CHECK = re.compile(r"S2S_ANT_FINAL_CHECK")
_INSERTED = re.compile(r"S2S_ANT_TOTAL_DIODES (\d+)")
_SKIP = re.compile(r"S2S_ANT_REPAIR_SKIP")
_ITER = re.compile(r"S2S_ANT_REPAIR_ITER (\d+)")
_AFTER_ITER = re.compile(r"S2S_ANT_AFTER_ITER\d+ remaining_nets=(\d+)")
_NET_VIOL = re.compile(r"Found (\d+) net violations")
_PIN_VIOL = re.compile(r"Found (\d+) pin violations")


def parse_repair_log(text: str) -> dict:
    """Parse the repair log for the summary metrics."""
    result: dict = {"completed": "S2S_ANT_REPAIR_DONE" in text, "skipped": bool(_SKIP.search(text))}

    # before counts from log (OpenROAD prints "Found N net/pin violations" after check_antennas)
    net_viols = _NET_VIOL.findall(text)
    pin_viols = _PIN_VIOL.findall(text)
    if net_viols:
        result["before"] = {"nets": int(net_viols[0]), "pins": int(pin_viols[0]) if pin_viols else 0}
    else:
        result["before"] = None

    # after counts: the last "Found N net/pin violations" in the log
    if len(net_viols) >= 2:
        result["after"] = {"nets": int(net_viols[-1]), "pins": int(pin_viols[-1]) if len(pin_viols) >= 2 else 0}
    elif result["skipped"]:
        result["after"] = result["before"]
    else:
        result["after"] = None

    m = _INSERTED.search(text)
    result["diodes_inserted"] = int(m.group(1)) if m else 0

    result["iterations"] = len(_ITER.findall(text))

    return result


class AntennaRepairError(RuntimeError):
    """The antenna repair tool could not run (never read as a pass)."""


def run_antenna_repair(odb: Path, workdir: Path,
                       repaired_odb: Path | None = None,
                       max_iterations: int = MAX_REPAIR_ITERATIONS,
                       timeout_s: float = 1800) -> tuple[dict, list[dict], list[dict]]:
    """Run the post-detailed-route antenna repair on a routed ODB.

    Args:
        odb: path to the routed ODB file
        workdir: working directory for logs and reports
        repaired_odb: if set, the repaired ODB is written here
        max_iterations: max repair iterations (each inserts diodes and re-routes)
        timeout_s: timeout for the OpenROAD process

    Returns (summary_dict, violations_before, violations_after).
    violations_before/after are parsed from check_antennas -verbose reports (same format as
    dfm.parse_antenna_verbose)."""
    workdir = workdir.resolve()
    sdir = workdir / ".s2s"
    sdir.mkdir(parents=True, exist_ok=True)

    rpt_before = workdir / "reports" / "antenna_repair_before.rpt"
    rpt_after = workdir / "reports" / "antenna_repair_after.rpt"
    rpt_before.parent.mkdir(parents=True, exist_ok=True)
    for rpt in (rpt_before, rpt_after):
        if rpt.exists():
            rpt.unlink()

    tcl = sdir / "antenna_repair.tcl"
    tcl.write_text(repair_tcl(odb, rpt_before, rpt_after, repaired_odb, max_iterations))

    cmd = ["openroad", "-exit", "-no_splash", str(tcl)]
    rec = runner.run(cmd, workdir, workdir / "logs" / "antenna_repair.log", "openroad", timeout_s)
    log = Path(rec.log_path).read_text(errors="replace")

    if rec.timed_out:
        raise AntennaRepairError(f"OpenROAD antenna repair timed out after {timeout_s}s; see {rec.log_path}")
    if rec.exit_code is not None and "S2S_ANT_REPAIR_DONE" not in log:
        raise AntennaRepairError(f"OpenROAD antenna repair did not complete; see {rec.log_path}")

    summary = parse_repair_log(log)
    summary["log"] = str(rec.log_path)
    summary["command"] = runner.command_str(cmd)
    summary["tool_version"] = rec.tool_version
    summary["duration_s"] = rec.duration_s

    before = dfm.parse_antenna_verbose(rpt_before.read_text()) if rpt_before.exists() else []
    after = dfm.parse_antenna_verbose(rpt_after.read_text()) if rpt_after.exists() else before

    return summary, before, after
