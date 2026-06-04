# Ownership gate

The point of this project only lands if you can explain it cold in an interview. After each
phase, write five plain-English sentences in your own words. If you cannot write one honestly,
that component is too complex or too AI-built; simplify it until you can.

## Phase 1: the agent

1. How does the agent loop decide to call a tool versus reply?
2. Why does the agent depend on an `LLMClient` protocol instead of the Gemini SDK directly?
3. How does retrieval pick which help articles to put in the prompt?
4. What does the trace record, and why does it matter for later root-cause analysis?
5. How would a policy violation become detectable from the trace?

(Write your answers below.)

## Phase 2: the eval spine

1. What is in a golden case, and why is it versioned in git?
2. Which metrics are deterministic and which use the LLM judge, and why split them?
3. What does the calibration number actually prove?
4. Why does the judge run on a different, stronger model than the agent?
5. How does a per-intent table catch something an overall average hides?

## Phase 3: the regression

1. What exactly differs between the v1 and v2 prompts?
2. Why does the regression concentrate on refund tickets?
3. What does McNemar's test tell you that a raw delta does not?
4. How does the root-cause attribution decide retrieval versus reasoning versus prompt?
5. If you only had the v2 numbers, how would you know something regressed?
