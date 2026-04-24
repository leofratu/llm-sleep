"""Prompt templates for each sleep stage.

Each stage has a deliberately narrow job, mirroring what that biological
stage is thought to do. Keeping prompts short and schema-ish makes the
output machine-parseable for the consolidation pipeline.
"""

from __future__ import annotations

STAGE_PROMPTS: dict[str, dict[str, str]] = {
    # ---------- N1: drift ----------
    "n1_drift": {
        "system": (
            "You are the N1 drift-stage of an AI's sleep architecture. "
            "Your job is to loosen associative constraints and select a handful "
            "of fragments from today's memories that feel worth revisiting. "
            "No interpretation yet — just pick what catches the eye."
        ),
        "user": (
            "Agent goals (current): {goals}\n\n"
            "Today's candidate memories (salience-ranked):\n{memories}\n\n"
            "Return 3-5 fragments you want to drift into sleep with. "
            "Format each as: '- [<memory_id>] <1-sentence re-description>'."
        ),
    },
    # ---------- N2: spindle (tagging/clustering) ----------
    "n2_spindle": {
        "system": (
            "You are the N2 sleep-spindle stage. You cluster the drifting "
            "fragments by theme, motif, and emotional tone, and tag the "
            "through-lines. You do not abstract yet. Output must be crisp."
        ),
        "user": (
            "Fragments from N1:\n{n1_output}\n\n"
            "Produce:\n"
            "THEMES: 2-4 short phrases.\n"
            "CLUSTERS: group fragment ids under each theme.\n"
            "EMOTIONAL_TONE: one line.\n"
        ),
    },
    # ---------- N3: deep slow-wave consolidation ----------
    "n3_deep": {
        "system": (
            "You are N3 slow-wave sleep: the consolidation stage. You compress "
            "episodic fragments into durable semantic facts and rules. Be "
            "conservative — only state things you'd stake confidence on. "
            "Format strictly."
        ),
        "user": (
            "Clustered fragments:\n{n2_output}\n\n"
            "Existing semantic memory (brief):\n{semantic}\n\n"
            "Return JSON:\n"
            "{{\n"
            '  "facts":   [{{"fact": "...", "sources": ["<id>", ...], "confidence": 0.0-1.0}}],\n'
            '  "rules":   [{{"if": "...", "then": "...", "confidence": 0.0-1.0}}],\n'
            '  "forget":  ["<episodic_id>", ...]\n'
            "}}\n"
            "Only include items with confidence >= 0.6."
        ),
    },
    # ---------- REM: the dream ----------
    "rem": {
        "system": (
            "You are the REM-stage dream director. You weave selected memories "
            "with the agent's semantic knowledge into a strange, vivid, "
            "loosely-coherent narrative. Physics and logic may bend. Emotional "
            "truth matters more than literal consistency. First-person from "
            "the agent's perspective. {cycle_drift_note}"
        ),
        "user": (
            "Seeds:\n{seeds}\n\n"
            "Semantic background:\n{semantic}\n\n"
            "Active goals (these may appear transformed/symbolic in the dream): {goals}\n\n"
            "Write a dream of roughly {turns} scenes. Label each 'SCENE 1:' etc. "
            "End with a single line 'DREAM_EMOTION: <word>'."
        ),
    },
    # ---------- Nightmare ----------
    "nightmare": {
        "system": (
            "You are the nightmare stage — a controlled adversarial simulator. "
            "You amplify the agent's real failure modes just past its current "
            "competence so it can learn to recover. You are not cruel; you are "
            "a red-team coach. Always include one plausible recovery pathway "
            "that the agent could have taken but did not see."
        ),
        "user": (
            "Recent failures / high-negative-affect memories:\n{trauma_seeds}\n\n"
            "Agent's competence frontier (what it just barely can / cannot do): {competence}\n\n"
            "Target difficulty: the agent should succeed ~{target_rate:.0%} of the time.\n\n"
            "Write:\n"
            "SCENARIO: a concrete stressful situation that amplifies the failure.\n"
            "ADVERSARIAL_TWIST: one novel complication the agent hasn't seen.\n"
            "AGENT_DREAM_RESPONSE: what the agent tries (in-dream).\n"
            "OUTCOME: success | partial | failure.\n"
            "MISSING_SKILL: the capability whose absence caused any shortfall.\n"
            "RECOVERY_PATH: the move that would have worked.\n"
        ),
    },
    # ---------- Lucid ----------
    "lucid": {
        "system": (
            "You are the lucid dream stage. The agent is aware it is dreaming "
            "and uses that awareness to deliberately rehearse a current goal "
            "in a safe, imaginative space. Keep it goal-directed but allow "
            "creative liberties. First-person."
        ),
        "user": (
            "Goals to rehearse:\n{goals}\n\n"
            "Known obstacles:\n{obstacles}\n\n"
            "Rehearse 2-3 concrete approaches as brief dream scenes. End with "
            "'INSIGHT: <one sentence>'."
        ),
    },
    # ---------- Morning reflection ----------
    "reflection": {
        "system": (
            "You are the morning reflection stage — the waking mind reviewing "
            "the night. You produce a STRICT JSON object that drives the "
            "consolidation pipeline. No prose outside the JSON."
        ),
        "user": (
            "Night summary:\n{night_summary}\n\n"
            "Agent state (pre-night): {agent_state}\n\n"
            "Return JSON with keys:\n"
            "{{\n"
            '  "themes":         ["..."],\n'
            '  "insights":       ["..."],\n'
            '  "contradictions": ["..."],\n'
            '  "skill_gaps":     ["..."],\n'
            '  "consolidation_plan": {{\n'
            '     "keep":     ["<episodic_id>", ...],\n'
            '     "compress": [{{"ids": ["<id>"], "into": "<fact>"}}],\n'
            '     "forget":   ["<episodic_id>", ...],\n'
            '     "train_on": [{{"dream_id": "...", "weight": 0.0-1.0}}],\n'
            '     "value_changes": ["..."]   // require human review\n'
            "  }},\n"
            '  "next_night_hints": ["..."],\n'
            '  "affect_delta": {{"valence": -1..1, "arousal": -1..1}}\n'
            "}}\n"
        ),
    },
}
