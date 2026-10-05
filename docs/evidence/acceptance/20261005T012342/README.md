# Failed first investigation acceptance attempt

This immutable run started from clean source
`fd47d3277132cb12554751ea223dc6af20d24d6f`.
Setup, browser setup, Blender version and security gates passed. The first full
suite recorded **664 passes and one failure** across 665 cases, with no skips.
The exact JUnit, coverage, log and original manifest remain here.

`tests/e2e/test_observability.py::test_metrics_timeline_and_dashboard_survive_restart`
still expected the removed presentation label `Causal timeline`. The redesigned
control is `Event timeline`; the underlying metrics, restart, reconciliation and
one-effect assertions passed. This was missed in the targeted UI checks.

The operator-owned acceptance process tree was stopped during the second suite
before changing source. That interrupted suite is not a result, and this run is
not accepted. No manifest or JUnit was edited to hide the failure. The follow-up
keeps every physical/persistence assertion, checks the intended label, and adds
structural assertions for the collapsed timeline, investigation dialog, evidence
and manual tabs, and reconciliation button. A new clean revision must run complete
acceptance twice and receive its own remote attestations.
