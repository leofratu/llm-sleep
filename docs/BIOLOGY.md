# How `llm-sleep` mimics real dreaming

This document explains, claim by claim, **what parts of biological
sleep this system is attempting to emulate**, how good the analogy is,
and where it breaks down. The goal is to be honest, not evangelical.

## 1. What biological sleep actually does

Modern sleep neuroscience converges on four functional roles:

1. **Memory consolidation** — hippocampal episodes are replayed during
   slow-wave sleep (SWS/N3) and transferred to neocortex as schemas.
   (Diekelmann & Born, 2010.)
2. **Synaptic homeostasis** — overall synaptic strength is *downscaled*
   in SWS, preferentially pruning weak connections so the signal-to-noise
   ratio of what remains improves. (Tononi & Cirelli, SHY hypothesis.)
3. **Offline simulation / emotional processing** — REM replays
   emotionally-tagged content, often in distorted form, and has been
   linked to fear-extinction and creative recombination.
   (Walker, Stickgold, Wagner et al.)
4. **Prediction-error replay** — hippocampal sharp-wave ripples
   preferentially replay *surprising* events; replays also run forward
   *and backward* and recombine trajectory fragments that never actually
   happened in sequence.

## 2. How each of those maps into `llm-sleep`

| Biology                         | `llm-sleep` analog                                            | File |
|---------------------------------|---------------------------------------------------------------|------|
| Hippocampal replay              | Salience-weighted sampler over `EpisodicMemory`               | `dreamer/memory/salience.py` |
| Prediction-error prioritization | `surprise = |reward − expected_reward|` term in salience      | `dreamer/memory/salience.py` |
| SWS consolidation               | N3 stage extracts `facts` + `rules` from clustered fragments  | `dreamer/stages/prompts.py` (`n3_deep`) |
| Synaptic downscaling            | `forget` list in N3 output + explicit "forget" action in plan | `dreamer/consolidation/gate.py` |
| Cortical schema formation       | `SemanticFact` store, merged nightly                          | `dreamer/memory/store.py` |
| REM recombination               | High-temperature multi-scene narrative bound to memory seeds  | `dreamer/stages/prompts.py` (`rem`) |
| REM emotional processing        | `valence`/`arousal` tags bias sampling; dream ends with `DREAM_EMOTION` | `dreamer/stages/prompts.py` |
| Fear extinction / rehearsal     | Nightmare stage targeted at high-negative-affect memories     | `dreamer/stages/prompts.py` (`nightmare`) |
| Lucid dreaming                  | Goal-directed rehearsal stage in the final cycle              | `dreamer/stages/prompts.py` (`lucid`) |
| Waking reflection               | Structured JSON reflection → consolidation pipeline           | `dreamer/stages/prompts.py` (`reflection`) |
| REM lengthening across night    | `rem_turns = base_rem * (1 + 0.3 * cycle_idx)`                | `dreamer/orchestrator/scheduler.py` |
| Sleep architecture cycling      | N1→N2→N3→REM loop, repeated `num_cycles` times                | `dreamer/orchestrator/scheduler.py` |

### Temperature as an analog of cortical entropy

In biology, neural firing during REM has higher entropy than during NREM
(closer to a wake-like state but disconnected from sensory drive). The
emulator mirrors this with explicit sampling temperature:

| Stage     | Temp  | Rationale                                                        |
|-----------|-------|------------------------------------------------------------------|
| N3 deep   | 0.2   | Consolidation must be conservative — low entropy, high confidence |
| N1 drift  | 0.3   | Slight loosening, but still grounded in real fragments            |
| N2 spindle| 0.4   | Tagging/clustering — some creativity in naming themes             |
| Reflection| 0.5   | Deliberate, reasoning-heavy                                       |
| Lucid     | 0.8   | Creative but goal-directed                                        |
| REM       | 1.0   | Maximum allowed by safe decoding; recombination > fidelity        |
| Nightmare | 1.1   | Adversarial, deliberately novel                                   |

### Salience ≈ hippocampal ripple prioritization

Hippocampal replay is not uniform: surprising, rewarding, and
recently-encountered events replay more. `score_memory` combines the
same signals:

```python
score = w_surprise * |reward - expected|
      + w_arousal  * arousal
      + w_recency  * exp(-Δdays / 2)
      + w_forget   * 1 / (1 + rehearsal_count)
      + w_goal     * goal_relevance
```

The `forget_boost` term is the anti-forgetting curve: memories that
haven't been rehearsed recently get a bump, which loosely matches
experimental findings that replay preferentially targets weakly-encoded
items during later sleep cycles.

### Nightmares as zone-of-proximal-development curriculum

Nightmares in the wild appear to be failed fear-extinction: the brain
re-surfaces a threatening scenario in an attempt to rehearse recovery,
but sometimes gets stuck. `llm-sleep` uses this productively: the
nightmare stage is explicitly **targeted at the agent's competence
frontier**, aiming for ~35% in-dream success rate, which is Vygotsky's
zone of proximal development and mirrors results from curriculum-learning
RL. Too easy → no growth signal; too hard → policy collapse.

Each nightmare must also output a `RECOVERY_PATH` — the move the agent
could have made but didn't. That's the extinction-learning payload.

## 3. Where the analogy breaks

Being honest:

- **No real neurons.** We're simulating the *functional roles*, not the
  mechanism. Spindles aren't involved; there's no actual synaptic
  downscaling.
- **The "dream" is just text.** A biological dream is multimodal,
  embodied, and recursively sampled from a generative model of the world.
  Our REM stage is a language model recombining text tokens. It's a
  caricature, not a simulation.
- **Replay is not trajectory-level.** Hippocampal replay operates on
  place-cell sequences with millisecond timing. Our "replay" is
  prose-level seed selection.
- **Consolidation is RAG, not weight updates.** In this POC we only
  modify a retrieval store. Real weight-level consolidation (LoRA / 
  fine-tuning on dream-generated data) is a downstream step gated behind
  human review.
- **No actual forgetting.** The POC marks memories as "forget-candidate"
  but does not delete them; true synaptic downscaling would need a
  decay rule on embeddings plus pruning.

## 4. Why it's still a useful proof of concept

Even with those caveats, four things work out of the box and are
independently testable:

1. **Structured offline compute** — the agent's memories are
   deterministically processed into higher-level facts without a human
   in the loop.
2. **Provider-agnostic stage routing** — you can run every stage on a
   different model, which enables ablations (does a stronger REM model
   produce better reflections?).
3. **Salience-weighted replay** — the same memories are *not* always
   selected, and the weights are tunable.
4. **Difficulty-targeted adversarial generation** — the nightmare stage
   is a controllable stress tester, useful on its own even outside this
   framing.

## 5. Evaluation plan (future work)

To show this isn't just theatre, the next steps are:

- **A/B against plain replay:** Agent performance on unseen tasks after
  N nights of dreaming vs. N nights of flat experience replay.
- **Ablations:** Remove nightmares / reflection / N3 independently.
- **Dream quality:** LLM-as-judge coherence + novelty + downstream
  utility score.
- **Cost curve:** $ per unit of downstream improvement — when does
  dreaming beat just training longer on the raw episodic data?

Without these, the system is well-engineered mimicry. With them, it
becomes a falsifiable claim.

## 6. Prior art worth reading

- Ha & Schmidhuber, *World Models* (2018).
- Hafner et al., *Dreamer V1–V3* (2020–2023).
- Schmidhuber, *Formal Theory of Creativity, Fun, and Intrinsic Motivation* (2010).
- Stickgold & Walker, *Sleep-Dependent Memory Triage* (Nat. Neurosci., 2013).
- Tononi & Cirelli, *Sleep and the Price of Plasticity* (Neuron, 2014).
- Wagner et al., *Sleep inspires insight* (Nature, 2004).
- Schaul et al., *Prioritized Experience Replay* (ICLR 2016).
