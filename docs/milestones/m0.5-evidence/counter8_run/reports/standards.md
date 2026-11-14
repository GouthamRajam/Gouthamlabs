# counter8 standards and IP report

## Result
**No external interface standard applies.** counter8 is an 8-bit up/down counter with synchronous reset, enable and load. It has no bus, serial link, or protocol interface.

## External references (implementation target, not interface standards)
| Item | Version | Source | Relevance |
|---|---|---|---|
| SKY130 PDK (sky130A) | release not pinned in this task | https://skywater-pdk.readthedocs.io/en/main/ (via kb-tk-003) | Process target. Tools check the rules; they are not restated here. |
| sky130_fd_sc_hd | high-density library, same PDK | same as above | Standard-cell library for synthesis and P&R. |

I did not access the web in this task, so there is no access date. The entries come from the knowledge base.

## Rules that matter for design and verification
These are good-practice rules from the KB, not standard requirements.
1. **Reset (kb-fc-004):** state the reset type (synchronous, per the request), active level, and the value of every output after reset. Reset every state element.
2. **Overflow/underflow (kb-fc-007):** state wrap or saturate at 0xFF up and 0x00 down, each with a testable criterion.
3. **Control priority (kb-fc-007):** define the order of reset, load, enable and direction.
4. **Spec checklist (kb-ck-001):** every requirement is typed and testable with a numeric criterion, and an out-of-scope list is present. Defaults are marked 'DEFAULT - needs G1 review'.
5. **Timing:** 100 MHz means a 10 ns period. Verification should include a clock constraint in the STA flow.

## Recommended defaults (DEFAULT - needs G1 review)
- Wrap on overflow and underflow.
- Priority: reset > load > enable; direction applies only when enable is set and load is not.
- Reset value of count = 8'h00.

## Reusable IP and license notes
- **No third-party IP required.** An 8-bit counter is trivial RTL and should be written in-house.
- Library cells in sky130_fd_sc_hd are covered by the PDK license, which is Apache-2.0 per the SkyWater PDK repository (my recollection, not verified here). The flow owner should confirm before tape-out.
- **Licensing risk for the CEO:** none identified. No paid or restricted IP is involved.

## Open issues
See the result's open_issues list. These are the spec gaps above and the unpinned PDK release.

## Checks
No tools were run in this task, so no pass/fail claims are made.
