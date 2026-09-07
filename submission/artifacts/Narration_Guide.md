# App walkthrough narration

Silent browser footage; captions are recording annotations. Add your own narration before submission.

## Short version (2:30)

### 0:00  The operator's question

DragonWings PAP helps an operator inspect additional solar availability. This demonstration uses synthetic telemetry and an actual local model run. It never commands equipment.

### 0:12  One selected run

The selected-run header links the decision to its saved evidence and records. Health checks the current service separately. The model name and attempt count identify the computation being inspected.

### 0:25  Inspect the actual model context

Context exposes the prompts and inputs sent to the model. Ordinary Python owns voltage checks, arithmetic, and publication authority. Model explanations cannot override those checks.

### 0:37  See which memory was selected

Memory shows selected and rejected guidance with similarity scores and reasons. Those scores rank relevance; they are not probabilities or proof that retrieved text is correct.

### 0:50  Search memory without changing history

A manual memory search has separate results. It does not replace the selected run's saved retrieval choices, so a reviewer can experiment without losing the explanation.

### 1:02  Follow the read-only tool calls

Tools shows the telemetry and weather calls, their status, and elapsed time. Their raw schemas, arguments, and results remain available. Both source tools are read-only.

### 1:15  Understand each model role

Subagent shows each role's provider, model, status, duration, and token usage. The optional third interpreter can be switched on or off to compare its contribution.

### 1:27  Inspect outputs and limits

Expanded model records expose inputs, output schemas, validated results, and limits. All roles share an eight-attempt budget. Failed or unsupported output cannot change calculated power.

### 1:40  Follow the workflow in order

Trace shows completed workflow steps in order. Routine cases use a linear path. Recorded solar overestimation can trigger bounded model reasoning, with the reason visible here.

### 1:52  Explain the search decision

Search details expose the alternatives considered and why the process stopped. A search limit explains termination; the selected guidance explains the resulting recommendation. They are separate facts.

### 2:05  Check the service independently

Health checks PostgreSQL, memory, workflow storage, source readiness, and model configuration. Cloud key presence is only a configuration check. It does not prove account access or answer quality.

### 2:17  Run the numerical preview

Finally, the numerical preview calculates the sunny fixture directly. It clears the previous selected run to prevent mixed evidence. The private repository contains code, tests, scripts, and capstone artifacts.

## Full version (9:00)

### 0:00  The operator's question

DragonWings PAP stands for Power Availability Profile. The operator's question is how much additional solar power may be available over the next twelve hours, and why that estimate should be considered. This is a working application, not a slide mockup. The recording uses a clearly labeled sunny fixture and a completed real local model run. The live MySolArk adapter is also implemented, but the fixed fixture makes this walkthrough repeatable. All equipment decisions remain with the operator. The application provides read-only evaluation guidance.

### 0:45  One selected run

The selected-run header is the starting point for debugging. It shows whether this recorded run published a profile or withheld it, the reported reason, and a link to the durable run. Reloading restores its result, evidence, memory, model records and workflow together. Health checks the current service separately. In Context, the model identity and attempt count tell us what was used. Reserved attempts include interrupted work, so they should not be confused with a count of successful answers. The result is historical evidence until another run acquires fresh inputs.

### 1:30  Inspect the actual model context

Expanding the details shows the actual system instructions and input context supplied to each model role. This is useful when an answer looks surprising: we can check what evidence the model received instead of guessing. The model is instructed to interpret supplied evidence and cite its identifiers. Numerical forecasting, power and energy arithmetic, voltage constraints, and final publication remain ordinary Python code. The roles have no equipment tools and no unrestricted database access. These records contain explicit inputs and validated outputs, rather than private internal reasoning.

### 2:15  See which memory was selected

The Memory tab separates stored knowledge from the context selected for this run. Guidance and explicitly indexed outcomes live in PostgreSQL with local vector embeddings. Retrieval ranks candidates by cosine similarity, then checks source, version, expiry, a minimum score, and duplicates. At most three records enter the model context. The summary shows why each candidate was selected or rejected. A similarity score is a ranking aid, not a probability or a truth guarantee. This makes retrieval decisions reviewable when an explanation relies on questionable context.

### 3:00  Search memory without changing history

A manual search lets an operator explore stored guidance, for example by asking about the voltage reserve. Its results are deliberately separate from the selected run's retrieval record. Searching now must not rewrite what a past model received. Index memory is also an explicit action: it includes newly eligible guidance or validated outcomes for future retrieval. This distinction matters for debugging and for evaluation. If memory changes between comparison trials, differences in the answers may come from changed context rather than from the model provider itself.

### 3:45  Follow the read-only tool calls

The Tools tab shows the source boundary. The graph uses two read-only MCP tools: one for current telemetry and one for the solar forecast inputs. The readable summary gives each call's name, result status, and duration. Expanding details reveals schemas, arguments, and returned evidence. Integration alone does not establish trust: typed validation and freshness checks still run before calculation. The live path reads the persisted MySolArk scrape through DW 1.24. Weather factors in this MVP are synthetic, which limits the forecast's operational usefulness and is stated in the interface.

### 4:30  Understand each model role

The Subagent tab summarizes the model calls by role. A generator proposes a small set of advisory interpretations. A critic scores surviving candidates using a fixed rubric. The optional interpreter runs before search and supplies separately validated advice. Python still rejects invalid candidates and selects the outcome within fixed bounds. Each record identifies the provider and model, status, elapsed time, and token usage when available. The current implementation supports local Ollama, OpenAI, and Claude through environment settings. Cloud adapter behavior has been tested with simulated HTTP responses; live cloud performance has not yet been measured.

### 5:15  Inspect outputs and limits

The expanded model record is the detailed debugging view. It includes the role's task, bounded input, requested schema, accepted output, and stopping limits. Each call has a forty-five-second timeout and a seven-hundred-sixty-eight-output-token cap, with no automatic retry. All roles share at most eight reserved attempts per episode. Attempts are stored before the call, so resuming an interrupted workflow does not silently call a provider again. Structured output is checked locally. Valid JSON alone is not proof of useful advice, so citations and deterministic authority remain necessary.

### 6:00  Follow the workflow in order

Trace explains how the components became one system. LangGraph acquires evidence, validates it, calculates the profile, assesses ambiguity, performs any required retrieval and model work, and reaches publication or withholding. The ordered list shows completed nodes with status and duration. Ordinary runs can remain model-free. Recorded solar overestimation above the demonstration threshold triggers selective reasoning. The assessment reason is visible above the list. During a new request, the interface shows elapsed time and a pending HTTP event; it does not claim to stream internal node progress before that information is returned.

### 6:45  Explain the search decision

The selective search considers a small set of advisory choices such as keeping the baseline, refreshing telemetry, or withholding guidance. It has three children per parent, a beam width of two, and only one refinement before final submission. The stored branch summaries show hard checks, scores, pruning reasons, and the selected guidance. The search stopping reason and the recommendation are separate facts: reaching a depth limit explains why work stopped, while the guidance explains what was selected. This is bounded, inspectable coordination, not an unrestricted autonomous planning loop.

### 7:30  Check the service independently

Health is a separate view of the current service. It checks the database, migrations, vector extension, semantic query, durable workflow storage, source freshness, and model readiness. A saved forecast may remain visible even when a current dependency is unavailable, so these states should not be confused. For cloud providers, readiness reports key configuration only; an actual call is needed to verify account access. The full local gate includes unit and integration tests plus Chromium Playwright checks. These support implemented behavior, while forecast accuracy and model usefulness still require broader, held-out evaluation.

### 8:15  Run the numerical preview

Finally, selecting the sunny fixture opens a source preview and clears the previous selected workflow. Calculate PAP runs the numerical core directly, making the solar-surplus calculation easy to inspect without model generation. The fixture has its own synthetic voltage floor; the live system uses the fixed observed floor of three hundred five point two volts. Neither setting is a calibrated state-of-charge model or a guarantee of future voltage. The repository is github.com/roboyak/PAP-Agent. It contains the implementation, setup instructions, teaching PRs, tests, reusable artifact scripts, and these recordings. Public access and narrated video hosting remain final submission steps.
