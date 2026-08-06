---
title: quantum_mechanics
authors:
- '[[stephen_hawking]]'
periods:
- '[[late_20th_century]]'
type: concept
tags:
- concept
created: 08/04/2026 12:24:42
updated: 08/04/2026 12:24:42
---

# quantum_mechanics

## Essence

A framework for describing matter and energy at microscopic scales, where probability and quantization are fundamental.

At the scale of atoms and subatomic particles, physical systems no longer have definite properties
until measured — instead, they exist in a superposition of possibilities described by a wave
function, and outcomes are inherently probabilistic rather than determined.

---

## Explanation

Classical physics assumes that a system has definite position, momentum, and other properties at
all times, whether or not anyone measures them. Quantum mechanics rejects this: a particle's state
is described by a wave function that assigns probabilities to different outcomes, and the act of
measurement appears to "collapse" this superposition into one definite result. This isn't just a
limit on what we can know — most interpretations treat the indeterminacy as a feature of reality
itself, not merely of our ignorance.

---

## Detailed Breakdown

- Underlying assumptions: physical states are described by probability amplitudes (wave functions), not definite values; certain pairs of properties (e.g. position and momentum) cannot both be known precisely at once (the uncertainty principle)
- Logical structure of the argument: predictions are statistical — the theory gives probabilities for outcomes of repeated experiments, not certainties for individual ones, yet matches experimental results with extraordinary precision
- Implications: undermines classical determinism and challenges naive realism about the properties particles have between measurements
- Counterpoints or alternate interpretations: multiple competing interpretations exist (Copenhagen, many-worlds, pilot-wave/Bohmian mechanics) that agree on the mathematics but disagree sharply on what is actually happening physically

---

## Criticism

- Common objections: Einstein's famous discomfort ("God does not play dice") with treating probability as fundamental rather than a placeholder for hidden variables
- Weaknesses in reasoning: the "measurement problem" — no consensus on what physically causes the wave function to collapse, or whether it collapses at all
- Rival interpretations: many-worlds avoids collapse entirely by positing that all outcomes occur in branching universes, at the cost of a vastly larger ontology
- Your personal doubts or questions: does quantum indeterminacy tell us something deep about free will and causation, or is it strictly confined to microscopic physics with no bearing on macroscopic human choice?

---

## Practical Use / Real-Life Reflection

Quantum mechanics underlies technologies from semiconductors and lasers to MRI machines and
(increasingly) quantum computing. Philosophically, it's the physics most often invoked — sometimes
too readily — in popular discussions of free will, consciousness, and the nature of reality, since
it's one of the few places physics itself abandons strict determinism.

## Related Movements

```dataview
TABLE title AS "Movement", periods AS "Period"
FROM "knowledge_base"
WHERE type = "movement"
AND contains(concepts, this.file.name)
SORT title ASC
```

## Books

```dataview
LIST FROM "knowledge_base"
WHERE type = "book"
AND contains(concepts, this.file.name)
```
