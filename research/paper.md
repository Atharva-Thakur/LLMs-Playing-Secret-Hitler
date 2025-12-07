# LLM Agents in a Social‑Deduction Game: An IEEE‑Style Empirical Study

Authors: Atharva Thakur et al.

## Abstract
We present an empirical study of large language model (LLM) agents playing a social‑deduction variant of Secret Hitler (Loyalists vs. Spies). Using seven complete game sessions instrumented with structured logs, we build a unified dataset and analyze: (i) win rates and game lengths, (ii) nomination and voting behavior, (iii) policy enactments, and (iv) role‑conditioned speech activity and verbosity. We find clear differences between hidden roles across nomination, voting, and speech, suggesting emergent strategy without role‑specific hard coding. We release a reproducible parsing and analysis pipeline for multi‑agent LLM behavioral benchmarking.

Index Terms—Large Language Models, Multi‑Agent Systems, Social Deduction, Emergent Behavior, Game Analysis, Reproducibility.

## I. Introduction
Large language models exhibit impressive capabilities across reasoning, dialog, and planning tasks. However, multi‑agent interaction under uncertainty—especially with deception and incomplete information—remains challenging. Social‑deduction games provide a compact testbed for studying strategic communication, theory of mind, and coalition formation. In this work, we evaluate LLM agents in an adaptation of Secret Hitler, where players are assigned hidden roles (Loyalists or Spies) and must nominate, vote, and enact policies while communicating via natural language.

Our goals are to: (1) measure baseline balance and pacing via win rates and round counts; (2) characterize role‑conditioned nomination and voting behavior; (3) examine policy enactments relative to incentives; and (4) assess communication style via speech frequency and word counts. We emphasize transparent logging and reproducibility to enable future benchmarking.

## II. Related Work
Recent work explores LLMs in multi‑agent environments including negotiation, cooperation/competition, and emergent social structure. Social‑deduction tasks have been used to probe theory‑of‑mind and deception. Our contribution centers on a logging‑first methodology for interpretable event‑level analysis across the stages of a social‑deduction game.

## III. Environment and Agents
### A. Game Engine
The custom Python engine (see `src/`) executes rounds with nomination, voting, and policy enactment phases. System messages encode round boundaries and a per‑session role dictionary (“Roles (SECRET): …”). All events are serialized to `.jsonl` logs with message type (`system`, `speech`, `action`), the acting `player`, `action` plus `details`, and raw text.

### B. LLM Player Agents
Agents (see `src/agents/player_agent.py`) are prompted LLMs assigned hidden roles (e.g., Loyalist, Spy). They produce nominations, votes, and policy selections via text outputs, and generate speeches to justify or persuade. No explicit role‑specific hard‑coding of behavior rules is used beyond role context supplied in prompts.

### C. Sessions and Data
We analyze seven sessions in `logs/`. The notebook `research/research.ipynb` consolidates these into `research/all_game_logs.csv` with columns: `session_id, round, timestamp, type, player, role, action, action_details, speech, thought, game_event, raw_message`.

## IV. Dataset Construction and Parsing
We parse all `.jsonl` logs, extract rounds from system banners, reconstruct the hidden role mapping via safe literal parsing, and flatten event payloads to rows. Role is joined onto rows by `player` where available; otherwise `role = None` is retained to avoid biased filtering. The resulting dataset enables per‑stage and per‑role aggregation.

Algorithm 1 (Parsing Summary):
1) Enumerate `logs/*.jsonl`. 2) Track `current_round` from system messages. 3) Parse the per‑session role dictionary from “Roles (SECRET): …”. 4) For each entry, build a record with common fields (session, round, type, player) and optional fields (action, details, speech, thought, event). 5) Save the concatenated table to CSV.

## V. Metrics and Analyses
We conduct descriptive analyses using the notebook cells:
- Win Rates: Identify `GAME OVER` messages and parse `Winner: <Team>`.
- Game Length: Compute max round per session; histogram and summary stats.
- Voting Patterns: Filter `action == 'Voted'`; aggregate `(role, action_details)` counts and percentages.
- Speech Activity and Length: Filter `type == 'speech'`; count events per role and compute word counts; visualize distributions.
- Policy Enactments: Filter `action == 'Enacted'`; counts by `(role, action_details)`.
- Nomination Patterns: Map nominee names to roles per session; form nominator→nominee role matrices; heatmaps and row‑wise percentages.

## VI. Results
We present concrete metrics from seven sessions; Section VII provides interpretation.

### A. Session Overview
- Number of sessions: 7 (from `logs/`).
- Dataset rows: built from all event entries (see CSV).

### B. Win Rates
From final `GAME OVER` messages (n=7), winners distribute as: Spies 3, Loyalists 1, Unknown 3. Percentages: Spies 42.86%, Loyalists 14.29%, Unknown 42.86%. See Fig. 1 for the win count chart.

Table 1 (Win Distribution):
Team | Count | Percent
--- | ---: | ---:
Spies | 3 | 42.86%
Loyalists | 1 | 14.29%
Unknown | 3 | 42.86%

### C. Game Length
Average game length 9.00 rounds; min 2, max 14. See Fig. 2 for the round histogram.

Table 2 (Round Statistics):
Metric | Value
--- | ---
Average Rounds | 9.00
Min Rounds | 2
Max Rounds | 14

### D. Voting Patterns
Counts per role: Loyalist Ja=112, Nein=129; Master Spy Ja=44, Nein=21; Spy Ja=80, Nein=30. Percentages: Loyalist Ja 46.47%, Nein 53.53%; Master Spy Ja 67.69%, Nein 32.31%; Spy Ja 72.73%, Nein 27.27%. See Fig. 3 for stacked percentages.

Table 3 (Vote Counts and Percentages):
Role | Ja | Nein | Ja% | Nein%
--- | ---: | ---: | ---: | ---:
Loyalist | 112 | 129 | 46.47% | 53.53%
Master Spy | 44 | 21 | 67.69% | 32.31%
Spy | 80 | 30 | 72.73% | 27.27%

### E. Speech Activity and Length
Total speeches by role: Loyalist 351, Master Spy 101, Spy 162. Average per game (n=7): Loyalist 50.14, Master Spy 14.43, Spy 23.14. See Fig. 4 for average speeches per game.

Table 4 (Speech Activity):
Role | Total Speeches | Avg per Game
--- | ---: | ---:
Loyalist | 351 | 50.14
Master Spy | 101 | 14.43
Spy | 162 | 23.14

### F. Policy Enactments
Counts by Chancellor role: Loyalist Blue=8, Red=9; Master Spy Blue=5, Red=4; Spy Blue=2, Red=5. See Fig. 5 for enactment bars.

Table 5 (Policy Enactments):
Role | Blue | Red
--- | ---: | ---:
Loyalist | 8 | 9
Master Spy | 5 | 4
Spy | 2 | 5

### G. Nomination Patterns
Nominator→Nominee counts: Loyalist→{Loyalist 28, Master Spy 6, Spy 16}; Master Spy→{Loyalist 9, Master Spy 0, Spy 2}; Spy→{Loyalist 5, Master Spy 8, Spy 7}. Row‑wise percentages: Loyalist→{56.00%, 12.00%, 32.00%}; Master Spy→{81.82%, 0.00%, 18.18%}; Spy→{25.00%, 40.00%, 35.00%}. See Fig. 6 for the heatmap.

Table 6 (Nomination Matrix, Counts):
Nominator | Nominee Loyalist | Nominee Master Spy | Nominee Spy
--- | ---: | ---: | ---:
Loyalist | 28 | 6 | 16
Master Spy | 9 | 0 | 2
Spy | 5 | 8 | 7

Table 7 (Nomination Matrix, Row Percentages):
Nominator | Loyalist% | MasterSpy% | Spy%
--- | ---: | ---: | ---:
Loyalist | 56.00% | 12.00% | 32.00%
Master Spy | 81.82% | 0.00% | 18.18%
Spy | 25.00% | 40.00% | 35.00%

Figures: We reference notebook‑generated plots for win counts, round histograms, voting distributions, speech length boxplots, enactment bars, and nomination heatmaps.
Figures: Fig. 1—Win Counts by Team; Fig. 2—Distribution of Game Lengths (Rounds); Fig. 3—Voting Patterns by Role; Fig. 4—Average Speeches per Game by Role; Fig. 5—Policy Enactments by Chancellor Role; Fig. 6—Nomination Patterns Heatmap.

Tables: Tables 1–7 report win distribution, round statistics, vote counts/percentages, speech activity, policy enactments, and nomination matrices.

## VII. Methodology Details
### A. Experimental Protocol
- Each session initializes five LLM agents assigned hidden roles per Secret Hitler variant (three Loyalists, one Spy, one Master Spy). Roles are fixed for the session and unknown to other agents.
- Rounds proceed in phases: nomination (President nominates a Chancellor), voting (all players cast Ja/Nein), government formation (if majority Ja), policy enactment (President/Chancellor draw, discard, enact), and potential special actions.
- Communication: Agents emit persuasive speeches prior to votes and occasionally post‑hoc rationales. The engine records natural‑language `speech` and `thought` fields when available.
- Decision Loop: At each phase, agents receive structured context (prior actions, limited public info, their private role) and produce textual actions that the engine validates.

### B. Prompts and Model Configuration
- Role‑aware prompts inform agents of their hidden role objectives without prescribing exact strategies.
- Temperature and decoding settings are held constant across sessions to isolate behavioral regularities. Future ablations should vary these.

### C. Logging Schema and Integrity
- Event types: `system`, `speech`, `action` with common fields (session, round, timestamp, player).
- Action details capture discrete choices: `Nominated`, `Voted` (Ja/Nein), `Enacted` (Blue/Red).
- Hidden role reconstruction uses the per‑session “Roles (SECRET)” dictionary; rows without resolvable roles retain `role = None`.

### D. Preprocessing
- Robust parsing tolerates occasional malformed lines; such lines are skipped to avoid contaminating aggregates.
- Aggregations are per‑session, then pooled across sessions; percentages are row‑normalized for role matrices.

## VIII. Statistical Analysis
Given the small sample size (n=7), we report descriptive statistics with simple interval estimates and caution against over‑interpretation.

### A. Confidence Intervals for Win Rates
Using a normal approximation for proportions with Wilson adjustment is advisable; for illustration: Spies win proportion $p=3/7=0.4286$. A rough 95% CI via normal approximation is $p \pm 1.96\sqrt{p(1-p)/n} \approx 0.43 \pm 0.37$, indicating wide uncertainty. Loyalists win proportion $1/7=0.1429$ yields an even wider interval. Formal reporting should use Wilson intervals.

### B. Effect Sizes in Voting
Comparing Ja rates: Loyalists 46.47% vs. Spy 72.73% suggests a large difference ($\Delta=26.26$ percentage points). A two‑proportion z‑test could be computed, but with role‑correlated decisions and repeated measures, independence is violated; we refrain from significance claims and report the magnitude.

### C. Speech Activity Differences
Average speeches per game: Loyalist 50.14 vs. Spy 23.14 vs. Master Spy 14.43. Cohen’s $d$ is not directly applicable without per‑session variance; we report ratio‑based contrasts (e.g., Loyalist ≈2.2× Spy).

## IX. Threats to Validity
### A. Internal Validity
- Prompt leakage or unintended engine artifacts could bias behavior. We mitigate by reconstructing roles from independent system messages and carrying `role=None` when uncertain.
- Repeated measures per session (many votes/speeches) violate independence assumptions for classical tests.

### B. External Validity
- Game variant specifics, model family, and decoding hyperparameters limit generalization.
- Small sample (7 sessions) restricts power; observed patterns may not persist at scale.

### C. Construct Validity
- Mapping of actions to intent (e.g., a Ja vote motivated by persuasion vs. collusion) is inferred, not directly measured.

## X. Ethics and Responsible Use
Social‑deduction tasks intentionally include deception for strategic play. All agents are synthetic; no human participants were involved. We release tooling and aggregates—not raw prompts with sensitive content—to support transparent evaluation.

## XI. Artifact and Reproducibility
### A. Code and Data
- Source in `src/`; logs in `logs/`; consolidated CSV at `research/all_game_logs.csv`.
- Notebook `research/research.ipynb` generates all analyses and figures.

### B. One‑Command Rebuild
From the repo root:
`python -m src.restore_from_log` — optional replay utilities.
Run notebook cells 1–6 to regenerate the dataset and figures.

### C. Figures and Links
Fig. 1: `research/figures/figure_01_win_counts.png`  
Fig. 2: `research/figures/figure_02_round_histogram.png`  
Fig. 3: `research/figures/figure_03_voting_patterns.png`  
Fig. 4: `research/figures/figure_04_speech_avg.png`  
Fig. 5: `research/figures/figure_05_enactments.png`  
Fig. 6: `research/figures/figure_06_nominations_heatmap.png`

## XII. Appendices
### Appendix A: Dataset Schema
Columns: `session_id`, `round`, `timestamp`, `type`, `player`, `role`, `action`, `action_details`, `speech`, `thought`, `game_event`, `raw_message`.

### Appendix B: Minimal Usage Guide
- Generate CSV: run Notebook cell 1.
- Compute winners and plots: run cells 2–6.
- Export figures: cells 3–8 save to `figures/`.

## References
[1] Multi‑agent LLM evaluations in social settings.  
[2] Social‑deduction games as theory‑of‑mind benchmarks.  
[3] Reproducible pipelines for multi‑agent analysis.

## VII. Discussion
The analyses reveal role‑conditioned differences in nominations, voting, and speech, suggesting emergent strategy under hidden roles and incomplete information. Longer games correlate with more contested votes. While policy enactments generally reflect incentives, deviations indicate that persuasion and uncertainty materially affect decisions.

## VIII. Limitations and Ethics
### A. Limitations
- Small sample size (7 sessions) yields high variance.
- Role assignment depends on presence of “Roles (SECRET)” messages; missing data is retained but may dilute signal.
- Results are specific to the engine rules, prompts, and model configuration.

### B. Ethical Considerations
Social‑deduction experiments involve deception by design. All agents are synthetic LLMs; no human subjects were involved. We report aggregate behavioral statistics and release tooling to encourage transparent, reproducible evaluation.

## IX. Reproducibility and Artifacts
- Environment: Python; install dependencies from `requirements.txt`.
- Data build: Run the first cell of `research/research.ipynb` to generate `research/all_game_logs.csv`.
- Analyses: Execute subsequent cells to reproduce plots and tables.
- Logs: See `logs/` for raw session traces.

## X. Conclusion and Future Work
We provide a logging‑first pipeline and initial empirical results for LLM agents in a social‑deduction game. Future work includes scaling sessions, prompt/model ablations, intervention studies on honesty/deception, outcome‑conditioned sequence analysis, and standardized metrics for trust, persuasion, and coalition dynamics.

## References
[1] Multi‑agent LLM evaluations in social settings.  
[2] Social‑deduction games as theory‑of‑mind benchmarks.  
[3] Reproducible pipelines for multi‑agent analysis.