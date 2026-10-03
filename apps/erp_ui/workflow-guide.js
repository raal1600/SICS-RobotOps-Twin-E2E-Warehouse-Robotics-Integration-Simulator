"use strict";
/* Presentation only. Decisions come from persisted workflow/verification records,
   never from the scene, replay frames or an expected scenario outcome. */
const SimulationGuide = (() => {
  const scenarios = {
    "": {
      label: "Happy path", phase: "Whole pick · no injected fault",
      meaning: "The baseline test: the planner supplies a valid plan, the controller moves the product and replies, and a fresh observation checks the result.",
      difference: "Use this to compare normal operation with a test that deliberately breaks one part of the workflow.",
      expected: "Expected: the machine moves the product to the destination and fresh evidence confirms completion."
    },
    DROP_ACK_AFTER_EFFECT: {
      label: "Lose acknowledgement after effect", phase: "Communication · after movement",
      meaning: "An acknowledgement is the controller's reply about a command. Here the pick happens and is recorded, but that reply is deliberately lost on its way back.",
      difference: "After effect means the product has moved. Before effect withholds a reply too, but the pick never starts. Both require evidence because silence alone cannot distinguish them.",
      expected: "Expected: the product moves, but the acknowledgement is lost. Review the original pick with a fresh observation before continuing."
    },
    DROP_ACK_BEFORE_EFFECT: {
      label: "Lose acknowledgement before effect", phase: "Communication · no movement started",
      meaning: "The controller records that the pick never started, and its reply is deliberately lost. The orchestrator receives no confirmation of that no-effect outcome.",
      difference: "Before effect keeps the product at source; after effect moves it. The same timeout appears in both, so the system must investigate instead of assuming failure.",
      expected: "Expected: no product movement and no acknowledgement. Review evidence to establish whether the original pick had any effect."
    },
    CONTRADICTORY_OBSERVATION: {
      label: "Contradictory observation", phase: "Verification · first check after movement",
      meaning: "After the pick, the simulated observation reports the same product in two different locations, such as source and destination. This tests handling of mutually conflicting detections.",
      difference: "The problem is conflicting locations. Low confidence is an unreliable report; stale evidence is an old capture time.",
      expected: "Expected: the product moves, but the observation conflicts. The outcome stays uncertain until sufficient fresh evidence resolves it."
    },
    LOW_CONFIDENCE_OBSERVATION: {
      label: "Low-confidence observation", phase: "Verification · first check after movement",
      meaning: "After the pick, the observation includes the product and a location, but its confidence score is deliberately reduced. This tests whether weak evidence is refused.",
      difference: "A detection is present but unreliable. Contradictory evidence gives conflicting locations; missing evidence gives no product detection at all.",
      expected: "Expected: the product moves, but observation confidence is too low. Review the original pick with another observation."
    },
    STALE_OBSERVATION: {
      label: "Stale observation", phase: "Verification · first check after movement",
      meaning: "Simulates delayed sensing by giving the post-pick observation an old capture time. Its location report may look plausible, but it is too old to establish the current outcome.",
      difference: "The problem is the report's age. A low-confidence report can be fresh but unreliable; a stale report has an unacceptable timestamp.",
      expected: "Expected: the product moves, but the observation is too old. Review the original pick with another observation."
    },
    LOGICAL_ESTOP: {
      label: "Logical E-stop", phase: "Cell control · before movement",
      meaning: "Simulates a deliberate stop request, like an operator pressing the simulator's stop control. The cell enters a stopped state and refuses the pick until reset. This is not safety-rated.",
      difference: "A requested stop. Cell fault instead simulates a detected error. Both block movement, but record different reasons and cell states.",
      expected: "Expected: the logical stop blocks the pick. The product stays still. Reset the logical cell before running another order."
    },
    CELL_FAULT: {
      label: "Cell fault", phase: "Cell control · before movement",
      meaning: "Simulates the controller detecting a cell error before movement. It marks the cell faulted and refuses the pick until the logical state is reset.",
      difference: "A detected error, rather than the deliberate stop request in Logical E-stop. Brain failures occur earlier, before a robot command is created.",
      expected: "Expected: a cell fault blocks the pick. The product stays still. Reset the logical cell before running another order."
    },
    BRAIN_INVALID_OUTPUT: {
      label: "Invalid Brain output", phase: "Planning · before command creation",
      meaning: "The Brain is the pick planner. This test supplies a reply that does not match the required action-plan format, so validation rejects it before a robot command can be created.",
      difference: "A reply arrives but is invalid. Brain timeout tests a planner that does not supply a plan within its deadline.",
      expected: "Expected: validation rejects the plan before dispatch. No product moves. Choose another scenario or repeat this rejection test."
    },
    BRAIN_TIMEOUT: {
      label: "Brain timeout", phase: "Planning · before command creation",
      meaning: "Simulates the pick planner missing its response deadline. The workflow handles the timeout before creating a robot command.",
      difference: "No plan in time, instead of the invalid reply tested by Invalid Brain output. Lost-ack scenarios happen later, after a command has been sent.",
      expected: "Expected: planning times out before dispatch. No product moves. Choose another scenario or repeat this timeout test."
    }
  };
  const observations = {
    "": {
      label: "Normal observation", phase: "Review capture · no injected sensing fault",
      meaning: "Collects a new observation of this test world without deliberately altering its detections, confidence or capture time. The verifier compares it with the original command journal.",
      difference: "Removes sensing degradation for this review only. It does not undo an execution fault or guarantee success: sufficient evidence can prove either completion or no effect.",
      expected: "Collect a fresh observation without injected degradation. The verifier still needs consistent evidence for this original command."
    },
    CONTRADICTORY_OBSERVATION: {
      label: "Contradictory evidence", phase: "Review capture · conflicting locations",
      meaning: "Reports the same product in two different locations in one observation. For example, it reports the product at both source and destination, even though the 3D product is not duplicated.",
      difference: "Conflicting detections. Low confidence supplies a weak detection; stale evidence has an old capture time; missing evidence has no product detection.",
      expected: "Inject conflicting evidence. Expect the pick to remain unresolved; you can observe again in this same test."
    },
    LOW_CONFIDENCE_OBSERVATION: {
      label: "Low confidence", phase: "Review capture · unreliable detection",
      meaning: "Includes a detected product and location, but deliberately lowers the confidence score. It represents a sensor report that is not reliable enough to trust.",
      difference: "The detection is present but weak. Missing evidence supplies no detection; contradictory evidence supplies incompatible locations.",
      expected: "Inject low confidence. Expect an inconclusive assessment; you can observe again in this same test."
    },
    STALE_OBSERVATION: {
      label: "Stale evidence", phase: "Review capture · old timestamp",
      meaning: "Gives the new capture an old timestamp to simulate a delayed sensor report. It tests the age of the evidence, even if the reported location looks plausible.",
      difference: "Too old to use, rather than low confidence or conflicting locations. This changes the observation timestamp; it does not rewind the 3D scene.",
      expected: "Inject an old capture time. Expect an inconclusive assessment; you can observe again in this same test."
    },
    MISSING_OBSERVATION: {
      label: "Missing evidence", phase: "Review capture · no detections",
      meaning: "Produces an empty observation with no detected products or location coverage, like a sensor that supplied no usable detections. The products remain in the 3D world.",
      difference: "No product detection at all. Low confidence still includes a detection. An absent detection cannot prove that the product was removed or that the pick failed.",
      expected: "Omit the product from the observation. Expect an inconclusive assessment; you can observe again in this same test."
    }
  };
  const catalog = kind => kind === "scenario" ? scenarios : observations;
  const explain = (kind, value) => catalog(kind)[value] || {
    label: "Unrecognized selection", phase: "Choose a supported option",
    meaning: "This selection has no documented simulation behavior.",
    difference: "Choose an option from the selector.", expected: "No expected result is defined for this selection."
  };
  const reasons = {
    CONTRADICTORY_OBSERVATION: "The observation gives conflicting locations for the product.",
    LOW_CONFIDENCE: "The observation is not confident enough to decide where the product is.",
    STALE_OR_FUTURE_OBSERVATION: "The observation time is outside the allowed freshness window.",
    MISSING_OBSERVATION: "The observation does not contain the product.",
    POSE_UNCERTAINTY: "The product position is too uncertain for verification.",
    CALIBRATION_MISMATCH: "The observation uses a different calibration.",
    SPATIAL_METADATA_MISMATCH: "The observation uses inconsistent spatial metadata.",
    SCENE_EPOCH_MISMATCH: "The evidence belongs to a different scene.",
    INSUFFICIENT_COVERAGE: "The observation does not cover all required locations.",
    OBSERVATION_PRECEDES_EFFECT_EVIDENCE: "The observation was captured before the recorded command outcome.",
    JOURNAL_UNAVAILABLE: "The original command journal is unavailable. An observation alone cannot confirm this pick.",
    JOURNAL_IDENTITY_MISMATCH: "The journal does not match the original command identity.",
    JOURNAL_OBSERVATION_CONFLICT_OR_INCOMPLETE: "The journal and observation disagree or do not provide enough evidence.",
    JOURNAL_AND_FRESH_DESTINATION_AGREE: "The original journal and fresh observation agree: the product reached the destination.",
    JOURNAL_AND_FRESH_SOURCE_PROVE_NO_EFFECT: "The original journal and fresh observation prove no pick effect. This order failed; a new order must be explicit."
  };
  function evidenceSummary(evidence) {
    const latest = evidence?.verifications?.at(-1);
    // Link to the exact assessed observation. A pre-pick planning capture is not
    // a fresh post-pick observation, even when it is last in the response array.
    const assessed = latest && (evidence.observations || []).find(item => item.observation_id === latest.observation_id);
    const reconciliation = latest && (evidence.reconciliations || []).find(item => item.verification.verification_id === latest.verification_id);
    const observation = assessed || reconciliation?.observation;
    const journal = evidence?.journal;
    const attempts = evidence?.reconciliations?.length || 0;
    return {
      journal: !evidence?.command ? "No robot command has been recorded."
        : !journal ? "Original command journal unavailable."
        : `Original command: ${journal.status}. Controller records ${journal.effect_count} pick effect${journal.effect_count === 1 ? "" : "s"}. This alone does not confirm the order.`,
      observation: observation ? `Assessed capture: ${observation.captured_at}.`
        : latest ? "The assessed observation is unavailable in this evidence response. Inspect the evidence details."
        : "No post-pick observation has been assessed yet. Collect fresh evidence to investigate the outcome.",
      decision: latest ? reasons[latest.reason] || `Recorded decision: ${latest.verdict} (${latest.reason}). Inspect the evidence details.`
        : "No verification decision yet. A lost acknowledgement does not establish failure.",
      attempts: `${attempts} review attempt${attempts === 1 ? "" : "s"} saved. Every assessment remains in the timeline.`,
      reason: latest?.reason || "AWAITING_VERIFICATION"
    };
  }
  function describe({ready, busy, archived, pending, state, cellMode, blocked, available, product, evidence}) {
    const result = (stage, tone, title, detail, action, label) => ({stage, tone, title, detail, action, label});
    if (!ready) return result(0, "neutral", "Loading your test", "Reading the saved world and workflow state.", "none", "Loading…");
    if (busy) return result(1, "neutral", "Operation in progress", "Watch the cell and recorded events. The next step appears when this operation finishes.", "none", "Working…");
    if (archived) return result(2, "neutral", "Viewing a saved test", "Review its outcome, evidence and full delivery replay here. Return to the current test to continue working.", "current", "Return to current test");
    if (pending) {
      const again = pending.state === "REQUIRES_INTERVENTION";
      return result(2, "attention", again ? `${product}: your review is needed` : `${product}: outcome uncertain`,
        again ? `${evidenceSummary(evidence).decision} Choose another observation in Review evidence to continue investigating this same pick.`
          : "The pick has no confirmed outcome. Review the original command and collect an observation. The next pick waits for this result.",
        "review", `Review ${product}`);
    }
    if (blocked) return result(1, "neutral", "Waiting for the active operation", "Another operation owns this cell. Its persisted outcome will determine the next step.", "none", "Waiting…");
    if (cellMode !== "READY") return result(3, "attention", "Reset the stopped cell", "The logical cell is stopped or faulted. Reset it here, then choose the next scenario. Reset does not move products or resolve uncertain jobs.", "reset", "Reset logical cell");
    if (available === 0) return result(3, "success", "Delivery finished", "All products are at the destination. Replay the full delivery, or start a new test with all products at source. Your choices and this result are saved.", "new-test", "Start new test");
    if (state === "COMPLETED") return result(3, "success", "Pick verified — continue when ready", "Choose the next product and scenario below, then run the next order. Use Start new test above for an independent combination with fresh products.", "configure", "Set up next pick");
    if (state === "FAILED") return result(3, "attention", "This pick did not complete", evidence?.command
      ? `${evidenceSummary(evidence).decision} Review the result, then choose the next scenario and run a new order explicitly.`
      : "Planning or validation stopped this order before a robot command was created. Review the causal timeline for the rejection, then choose the next scenario or repeat this test.", "configure", "Choose next scenario");
    return result(0, "neutral", "Ready for your first pick", "Choose a product and execution scenario below. Run the order, watch the cell, then follow the next step shown here.", "configure", "Choose product & scenario");
  }
  return {describe, evidenceSummary, explain,
    choices: kind => Object.entries(catalog(kind)).map(([value, info]) => ({value, ...info})),
    scenario: value => explain("scenario", value).expected,
    observation: value => explain("observation", value).expected};
})();
if (typeof module !== "undefined") module.exports = SimulationGuide;
