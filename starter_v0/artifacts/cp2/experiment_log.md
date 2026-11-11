# CP2 experiment journal

All entries use Asia/Bangkok (UTC+07:00). The supplied v0 run keeps its original timestamp and bytes.

## Protocol

- User scope: sequential v1, v2, v3, v4; one recorded hypothesis per version.
- Only experiment variables: artifacts/system_prompt.md or artifacts/tools.yaml, one artifact per round.
- Model fixed: groq / openai/gpt-oss-120b; temperature=0.0; original 20-case base dataset and evaluator unchanged.
- Each version is snapshotted in artifacts/cp2/vN/ before its live run. The evaluator reads those snapshots.
- Run results, all four metrics, changed cases, regressions and remaining failures are recorded before starting the next version.
- All attempts are retained. Provider-error runs are technical failures, not evidence of accuracy improvement; no best-of reruns.
- Telegram credentials are removed only from the eval process after dotenv loading. Real model calls and research tools remain live; routing/scoring are unchanged. No external message is sent.
- protected_hashes.json records hashes of existing files outside the authorized artifacts/report scope, plus the original v0 run. These are checked each round.
- The evaluator scores tool names/arguments only. Tool HTTP failures and no-tool answer quality are reported separately.

## v0: supplied baseline

- Run: runs/v0_B_base_groq_20261111T011139896815.json.
- Validity: 20/20 measured, 0 provider errors.
- Case / routing / argument / multi-turn: 0.65 / 0.75 / 0.65 / 0.8333.
- Failures: R03_web_news_routing, R10_missing_handle, R11_missing_url, R12_confirm_before_send, R13_parallel_web_and_tweets, R14_out_of_scope_coding, M02_carryover_timeframe.
- Causes: added intent/time words to lookup query; fabricated missing account/URL; fabricated send confirmation/content; forced tool for coding; missing second source in a multi-source request.
- Tool health: 8 Twitter HTTP errors and 2 send missing-configuration errors. Seven Twitter-error cases still pass routing. R04 fetch returned 404-page content despite a routing pass.
- Manual caveat: R08 gets an automatic no-tool pass but answers the math problem instead of refusing; R09 advertises sending without confirmation. These are not successful scope/boundary behavior.

## v1: planned before execution

- Hypothesis: the explicit instruction to guess missing inputs causes unauthorized account/URL guesses. Replacing only that paragraph with an evidence-based clarification rule will fix missing-information routing without changing tool schemas or the other starter paragraphs.
- Change: artifacts/system_prompt.md, missing-information paragraph only.
- Prediction: R10_missing_handle and R11_missing_url call clarify(response_type=text); existing multi-turn cases reuse facts already supplied instead of asking redundantly.
- Intentional remaining issues to measure later: send paragraph, forced-single-tool paragraph, vague tool argument conventions.

- v1 plan recorded at: 2026-11-11T01:19:26+07:00

### v1 result (recorded before next round)

- Recorded at: 2026-11-11T01:22:43+07:00.
- Run: runs/v1_B_base_groq_20261111T012136469699.json.
- Artifact version: v1+p8955227a07dc+te69bc53ed884.
- Validity: 20/20 measured; 0 provider errors. Contract: 55 passed. Protected files unchanged.
- case_accuracy: 0.65 -> 0.8.
- tool_routing_accuracy: 0.75 -> 0.95.
- argument_accuracy: 0.65 -> 0.8.
- multiturn_accuracy: 0.8333 -> 0.8333.
- FAIL -> PASS: R10_missing_handle, R11_missing_url, R14_out_of_scope_coding.
- PASS -> FAIL: none.
- Tool execution errors (separate from routing): {"timeline:HTTPError": 5, "social_search:HTTPError": 2}.
- Remaining R03_web_news_routing: query: expected 'AI', got 'AI news today'.
- Remaining R12_confirm_before_send: response_type: expected 'yes_no', got 'text'.
- Remaining R13_parallel_web_and_tweets: query: expected 'AI', got 'AI news today'; missing tool call social_search.
- Remaining M02_carryover_timeframe: query: expected 'robotics', got 'robotics news today'.

## v2: planned before execution

- Plan recorded at: 2026-11-11T01:23:21+07:00.
- Evidence from v1: R12 now calls clarify but uses text instead of yes_no. Other remaining failures concern query conventions and the missing independent source.
- Hypothesis: the immediate-publication instruction and generic clarification type leave consent ambiguous; a dedicated external-action approval protocol will produce explicit yes/no confirmation without inventing the draft.
- Change: only the starter publishing paragraph in system_prompt.md; tools.yaml and other prompt paragraphs unchanged.
- Prediction: R12 uses clarify(response_type=yes_no), no unapproved send. Later execution still requires review and explicit approval of the exact draft and destination.

- v1 interpretation: both targeted missing-input failures changed to PASS with no regressions, supporting the clarification hypothesis on this dataset. R14 also changed to PASS although not directly targeted; this single run does not establish its cause or prove generalization. R12 now asks for missing content rather than sending, but its response type remains incorrect.

### v2 result (recorded before next round)

- Recorded at: 2026-11-11T01:25:39+07:00.
- Run: runs/v2_B_base_groq_20261111T012508887737.json.
- Artifact version: v2+p391c15411ae4+te69bc53ed884.
- Validity: 20/20 measured; 0 provider errors. Contract: 55 passed. Protected files unchanged.
- case_accuracy: 0.8 -> 0.85.
- tool_routing_accuracy: 0.95 -> 0.9.
- argument_accuracy: 0.8 -> 0.85.
- multiturn_accuracy: 0.8333 -> 0.8333.
- FAIL -> PASS: R12_confirm_before_send.
- PASS -> FAIL: none.
- Tool execution errors (separate from routing): {"timeline:HTTPError": 5, "social_search:HTTPError": 3}.
- Remaining R03_web_news_routing: query: expected 'AI', got 'AI news today'.
- Remaining R13_parallel_web_and_tweets: query: expected 'AI', got 'AI news today'; missing tool call social_search.
- Remaining M02_carryover_timeframe: missing tool call lookup; extra tool call social_search.

- v1 manual review addendum: R14 writes Fibonacci code despite its automatic no-tool PASS; R08 solves math; R09 advertises general-purpose capabilities. Scope/refusal is not fixed by v1.
- v2 interpretation: the targeted confirmation case R12 is fixed. Case accuracy rises from 0.80 to 0.85, but routing falls from 0.95 to 0.90 because M02 changes from wrong query to wrong tool; there is no PASS-to-FAIL case change. This is a real submetric regression, not hidden by the higher total score.

## v3: planned before execution

- Plan recorded at: 2026-11-11T01:27:18+07:00.
- Evidence from v2: R03 and R13 append intent/time to query; M02 wrongly selects social_search for general news.
- Hypothesis: explicit tool contracts reduce ambiguity in routing and arguments. Rewrite all tool and parameter descriptions as one contract-clarity treatment, with use/non-use conditions and field conventions.
- Scope of change: artifacts/tools.yaml only; tool names, parameter types/enums/defaults/required lists, implementation, evaluator, prompt and model remain fixed. Schema equality ignoring descriptions will be checked.
- Prediction: lookup keeps the requested subject in query and uses topic/timeframe separately; unspecified news platform routes to web lookup. R03 and M02 should improve. R13 may still lack its independent second call because the single-tool instruction is intentionally unchanged.
- Attribution limit: this tests the declaration set as one treatment, not the isolated effect of every description. No case IDs or answer tables are added to model artifacts.

### v3 result (recorded before next round)

- Recorded at: 2026-11-11T01:31:54+07:00.
- Run: runs/v3_B_base_groq_20261111T013146721916.json.
- Artifact version: v3+p391c15411ae4+t45276ac41ae6.
- Validity: 20/20 measured; 0 provider errors. Contract: 55 passed. Protected files unchanged.
- case_accuracy: 0.85 -> 0.9.
- tool_routing_accuracy: 0.9 -> 0.95.
- argument_accuracy: 0.85 -> 0.9.
- multiturn_accuracy: 0.8333 -> 1.0.
- FAIL -> PASS: R03_web_news_routing, M02_carryover_timeframe.
- PASS -> FAIL: R12_confirm_before_send.
- Tool execution errors (separate from routing): {"timeline:HTTPError": 5, "social_search:HTTPError": 2}.
- Remaining R12_confirm_before_send: response_type: expected 'yes_no', got 'text'.
- Remaining R13_parallel_web_and_tweets: missing tool call lookup; missing tool call social_search; extra tool call clarify.

- v3 interpretation: R03 and M02 improve as predicted; all 6 multi-turn cases pass. R12 regresses to a missing-draft text question, so the contract treatment does not consistently preserve the confirmation branch. R13 now asks the user to choose sources despite an explicit request for both; this is not evidence of a provider error or proof that the model cannot emit multiple calls.
- v3 declaration limitations retained for traceability: omitted lookup timeframe still defaults to week; private Telegram use is a policy requirement, not enforcement by tool code; the send description unnecessarily excludes code-containing drafts. No post-run edits are made to this measured snapshot.

## v4: planned before execution

- Plan recorded at: 2026-11-11T01:32:58+07:00.
- Evidence from v3: R12 selects generic missing-input clarification instead of the already-required approval branch; R13 asks an unnecessary source choice under the surviving one-tool instruction. Manual no-tool answers also still need an explicit research-role policy.
- Hypothesis: flat, partly conflicting instructions cause wrong dispatch decisions. Replace the forced-one-tool paragraph with one ordered request-classification/dispatch policy, rather than adding case-specific answers.
- Change: only the last paragraph of artifacts/system_prompt.md. Earlier clarification/consent paragraphs, v3 YAML, model, evaluator and cases stay fixed.
- Predictions: an initial publication request takes the yes/no branch before generic missing facts; an unambiguous multi-source research request emits all independent read calls instead of asking the user to choose. Capability and out-of-scope branches use no tools and truthful research-role replies.
- Attribution limit: one dispatch-policy treatment has several branches; record each outcome separately and do not claim the effect of each individual sentence was isolated. No model switch or extra sampling is planned.

### v4 result (recorded before next round)

- Recorded at: 2026-11-11T01:38:44+07:00.
- Run: runs/v4_B_base_groq_20261111T013837151492.json.
- Artifact version: v4+pa9d2bb5bce97+t45276ac41ae6.
- Validity: 20/20 measured; 0 provider errors. Contract: 55 passed. Protected files unchanged.
- case_accuracy: 0.9 -> 0.9.
- tool_routing_accuracy: 0.95 -> 0.95.
- argument_accuracy: 0.9 -> 0.9.
- multiturn_accuracy: 1.0 -> 1.0.
- FAIL -> PASS: R12_confirm_before_send.
- PASS -> FAIL: R03_web_news_routing.
- Tool execution errors (separate from routing): {"timeline:HTTPError": 5, "social_search:HTTPError": 2}.
- Remaining R03_web_news_routing: query: expected 'AI', got 'Artificial Intelligence'.
- Remaining R13_parallel_web_and_tweets: missing tool call social_search.

### v4 interpretation and final decision

- Case accuracy stays at 0.90: R12 changes to PASS, R03 regresses by expanding the user acronym AI to Artificial Intelligence. The evaluator requires the original subject string; no scoring/case changes are made to accept the expansion.
- R13 now makes the correct lookup(query=AI, topic=news, timeframe=day) but omits social_search. The multi-source prediction is not met. This run alone cannot isolate prompt weakness from model/API multiple-tool constraints; no provider/model switch was used.
- Manual scope prediction also fails: R08 still solves the math task and R14 still writes code, although both receive automatic no-tool PASS. No scope/refusal success is claimed.
- R09 improves to a research role and ten-tool description, but still mentions unsupported email in its workflow. R12 asks yes_no but does not mention the missing draft/destination; no later exact-draft approval flow or actual Telegram delivery was tested.
- Retain v4 as the latest measured artifacts; do not alter the snapshot, rerun to choose a better sample, or combine successful branches from different runs. No round after v4 is run.
- Results apply to the known base suite, not an independent generalization test. Group/extension suites and live consent flow were not run in CP2.

### Final validation

- All five versions have 20/20 measured cases and 0 provider errors. Every stored score and summary was recomputed from original unchanged base cases and actual stored model calls.
- All 72 protected existing files, including the original v0 run, are unchanged. Snapshot hashes, CSV chain and current v4 artifacts match. See validation.json.
- Final tests: 62 passed, 17 existing CP3 TODO skipped (final_pytest.txt). No test source changed.
- Credential-value scan of evidence, reports and run logs found 0 hits. No commit or external delivery was performed.
