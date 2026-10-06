# Response and body synchronization correction

The original source A campaign remains failed. This subarchive records the later test/ADR correction, its exact source hashes and diff, and bounded validation; it does not relabel that dirty corrective source as clean A.

Four existing browser lifecycle cases passed (SyntheticRuntime and BlenderRuntime, desktop and compact), followed by one controlled repeat of the same desktop SyntheticRuntime case. The repeat held the successful clear response body for5.265s after headers and passed its unchanged correctness/UI/teardown assertions. These are four unique pytest cases, not five. Three separate native clear probes are diagnostic operations, not pytest cases.

Native probes did not reproduce the original4.914s HTTP wait; its cause remains unproven. Product behavior, mutation retry policy,20s request budget and5s UI assertions remain unchanged. Root lint/type/drift receipts and independent static reviews are preserved with their original scopes and times.

inputs.json hashes copied bytes. Source/scripts are inert .txt copies. The five small browser JSONs preserve requests/errors/source hashes; no new ZIP, screenshot or DOM review was performed. Empty stderr files are recorded, not copied. Parent baseline summary/index/root-review remain unchanged. Root review is required before commit; fresh full acceptance and remaining final proof are still pending.
