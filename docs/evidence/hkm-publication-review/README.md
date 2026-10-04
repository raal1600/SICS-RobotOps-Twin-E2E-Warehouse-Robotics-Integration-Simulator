# Historical deployed publication review

This review inspected the public publication for source commit
`0d8a8dbf72b063f43f7ca80460a7b67c577172e9` on 4 October 2026.
It passed its scoped artifact checks. **It is not final system acceptance and does
not attest later source revisions.** The reviewed publication correctly retained
`NOT DONE` while full acceptance was pending.

## Public resources and retained evidence

The [deployed build manifest](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/build.json)
identified that exact source commit. The [combined PDF](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/downloads/robotops-twin-samlat.pdf),
three individual report PDFs, and design, sources and diagrams pages all returned
HTTP 200. These URLs follow the current deployment and may change after this review.

Retained here are the original [manifest](build.json), original
[combined PDF](robotops-twin-samlat-0d8a8db.pdf),
[machine-readable result](result.json), and one
[rendered tool-preparation page](tool-preparation-page-22.png).
The result records every fetched URL, timestamp, size and SHA-256. No publication
content was manually edited. Full contact sheets and additional detailed renders
remain in ignored `artifacts/hkm-publication-review/public-0d8a8db/`.

| Artifact | Pages | SHA-256 |
| --- | ---: | --- |
| Design report | 33 | `514fc631e91130fd517e51a8541d3120036a7348dc22521aa3e59a8c49283001` |
| Scope report | 13 | `01812be919d7927366c8896e355ca7c6eb50e0f46f0ec7f1c763e5301d3659e0` |
| Discussion report | 17 | `84cb853dfea45a1e1b7018bd1cf618fc08e406896c14736e96569bd42f13fafc` |
| Combined report | 63 | `b34a9d713a8a39a749c1ee0e0f61285ac90ebbdde3caedcff4fa90827271724b` |

## Checks and limits

All individual PDF hashes matched the deployed manifest. All 200 combined-PDF
internal links resolved to the same destinations as the individual reports
(83 + 58 + 59). The manifest reported 30 sources and 11 diagrams. Every page had
the corrected `4 oktober 2026` footer, with no replacement glyphs in extracted text.

All 63 pages were reviewed as rendered contact sheets. Pages 11, 18, 20, 21, 22,
23 and 24 were inspected at full size for the architecture, observation boundary,
HKM-inspired cell, compatibility matrix, tool preparation, frames and runtime
boundary. No clipped text or overflowing tables were observed. The implemented
captions retain the pending-acceptance qualification, and tool engagement correctly
says **dock empty**. Rendering used Poppler; extraction and link checks used pypdf.
Commands and scoped observations are recorded in `result.json`.

The public Linux build has 63 pages; the earlier Windows working-tree build had
61. Rendering bytes are not compared across platforms. External research sites
were not re-fetched during this layout review. This archive is immutable historical
evidence; new publication verification belongs to the revision it actually checks.
