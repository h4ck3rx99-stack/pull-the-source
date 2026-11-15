# 60-second outline + judge questions

## 60 seconds
- **0–10 s, hook.** "An AI recommends a product and cites six sources. One source gets retracted. Does the recommendation change when it should, and only when it should?"
- **10–25 s, method.** 12 fictional purchase scenarios. From the same recorded first answer we pull one source three different ways: the one the recommendation needs, an irrelevant one, and one that has a backup. Two of the three should change nothing, so a model that just panics and abstains scores 12 out of 36.
- **25–35 s, intervention.** Half the runs use an ordinary prompt; half must keep an explicit table of which requirement rests on which source.
- **35–50 s, result.** 96 real calls to Claude Haiku. Ordinary prompt: 36 of 36. Dependency table: 35 of 36. The single miss was the table condition being over-cautious on an item we now think is ambiguous. Null result: the table did not help, because there was nothing to fix.
- **50–60 s, why it matters / demo.** The value is the protocol: frozen, hashed, controls against abstention, raw outputs released. Click "Withdraw" in the demo to replay any recorded run. Next step is making it hard: no stated rule, buried retractions, multi-hop dependencies.

## Five likely judge questions
1. **"Everything is at ceiling. What did you learn?"** That on short, explicit cases this model propagates withdrawals correctly in both directions, and that a dependency table adds nothing there. It bounds where the problem is not. We say plainly that it does not show robustness in harder settings.
2. **"How is this different from DeReLab or PALIMPSEST?"** It is much smaller and overlaps in the question. Our specific angle is withdrawal of support (nothing new asserted), the paired irrelevant and redundant controls from one shared starting point, and a prompt-level intervention. PALIMPSEST uses the same "withdrawn means unknown" semantics with an external store; we test an in-context table.
3. **"Is 12 scenarios enough?"** Enough to run a clean pilot, not enough to detect small effects. We report counts, treat the scenario as the unit, and the sign test on 1 discordant pair is p = 1.0. One sample per cell, so no variance estimate.
4. **"Could the model have seen the answer key?"** Keys were stored separately, never included in prompts (the self-check asserts this), and moved out of the working folder during collection. Each call was told to read one prompt file. Caveat: calls ran in an agent harness, and 11 of 96 made a stray unrelated tool call; we logged them and did not rerun.
5. **"Your one failure — is the model wrong or is your key wrong?"** Arguably the key. "1180 W on high" does not strictly say high is the maximum. We scored it wrong because the key was frozen, and we report the ambiguity. Changing the key after seeing results would be worse.

Backup: **"Who did the work?"** Protocol, data, code and runs were produced with Claude under our direction on 15 Nov; we reviewed [team: state what you personally checked].
