# RobotOps Twin

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users and purpose

Systems engineers use this local simulation to run a warehouse pick, follow the
integration from business request to robot and back, and investigate saved evidence.
The user explicitly requires first-time clarity and efficient expert inspection.

## Capabilities and constraints

The existing FastAPI application serves vanilla JavaScript and CSS. Guided execution
has 22 persisted boundaries. The browser requests permitted operations; backend state
remains authoritative. An uncertain physical outcome must be reconciled against the
original command, never turned into a new pick by navigation or retry wording.

The native integration lab uses PostgreSQL, RabbitMQ, HTTP and OPC UA with simulated
systems. Local fixtures use simulated transports. The PLC is Python, not a supplied
vendor ladder or Structured Text program. Blender replay is recorded illustration,
not sensor verification, validated robot dynamics, or a certified safety function.

Test history, fault scenarios, explicit physical authorization, recovery, replay,
engineering records, current component source, saved excerpts, and JSON exports must
remain reachable. Saved tests remain read-only under existing backend permissions.

## Product principles

- Show what happened, what is proven, what remains uncertain, and the next permitted action.
- Keep execution and historical inspection separate and visibly identified.
- Retain detailed technical evidence behind clear, short labels.
- Preserve selection when moving between the robot view and evidence.
- Explain failures in ordinary language while retaining exact codes and records.

## Accessibility and inclusion

Target applicable WCAG 2.2 AA criteria. Support keyboard operation, visible focus,
text enlargement, narrow screens, reduced motion and text alternatives to the 3D view.
Automated checks do not establish complete conformance. Record manual testing limits.

## Assumptions

Desktop/laptop is the primary engineering workspace; narrow screens must remain usable
for inspection and controls. English is the current product language. Preserve the
established dark, teal-accented identity and system font stack. These reversible choices
follow repository evidence and the user's explicit authorization to decide without
routine approval. No new authentication or external service is introduced.

## Operating documentation

See [engineering inspection](docs/implementation/engineering-inspector.md),
[evidence workbench](docs/implementation/evidence-workbench.md), and
[investigation](docs/implementation/investigation.md) for the domain contracts.
