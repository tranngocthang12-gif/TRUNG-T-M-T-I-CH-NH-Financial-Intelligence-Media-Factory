# UNIVERSAL ML FACTORY - Bootstrap (migration candidate)

Read in this order before any substantive architecture or runtime work:

1. `PROJECT_CHARTER.md` - immutable mission, delegated authority, financial legacy boundary.
2. `PROJECT_STATE.json` - exact candidate state and current blockers.
3. `ARCHITECTURE.md` - shared/core/task/domain topology and gate order.
4. `PROJECT_HANDOFF.json` - concrete next action, never historical finance work.
5. `docs/adr/` and task/domain contracts.

The canonical owner-approved Factory Supreme Laws 1-26 and prior ADR-001/002 are held in the Project Library until this migration is reviewed and accepted. Never treat this migration draft as modifying those laws. If a check contradicts the Library canonical state, stop and resolve authority before writing.

The old `governance/OWNER_MISSION.md`, `governance/SAFETY_STATE.yaml`, financial `config.yaml`, and former `engine/` remain a protected legacy financial domain. They do not grant the new Factory any authority to trade, spend, publish, auto-promote, or auto-retrain.

Use `python tools/validate_factory.py` and `python -m unittest discover -s tests -p 'test_factory_*.py' -v` to check this branch. Never claim an offline green test proves real ML performance, independent critic identity, owner acceptance, production readiness or current remote live liveness.
