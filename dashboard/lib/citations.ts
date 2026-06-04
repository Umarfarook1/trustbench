// Real, verifiable sources only. Each entry is referenced inline by id in the narrative.
// Keeping these honest is the point: citing something fake to a founder is disqualifying.

export type Citation = {
  id: string;
  n: number;
  label: string;
  source: string;
  url: string;
  note: string;
};

export const CITATIONS: Citation[] = [
  {
    id: "fini-trust",
    n: 1,
    label: "Trust Metrics for AI Customer Support: Why Deflection Rate Is Killing Your CX",
    source: "Fini (usefini.com)",
    url: "https://www.usefini.com/blog/trust-metrics-for-ai-customer-support-why-deflection-rate-is-killing-your-customer-experience",
    note: "Fini's own argument that deflection is a vanity metric and resolution is what matters. This project measures resolution, and names its metrics after Fini's seven trust dimensions.",
  },
  {
    id: "fini-ragless",
    n: 2,
    label: "RAGless: the accuracy-first architecture for support",
    source: "Fini (usefini.com)",
    url: "https://www.usefini.com/blog/what-is-ragless",
    note: "Fini frames support as a reasoning and workflow problem, not a document-retrieval problem. The agent here reasons over policy and takes tool actions, not just retrieves text.",
  },
  {
    id: "paramount",
    n: 3,
    label: "Paramount: ground-truth capture and regression testing for AI",
    source: "ask-fini, GitHub (GPL-3.0)",
    url: "https://github.com/ask-fini/paramount",
    note: "Fini open-sourced a tool that records AI outputs, has experts label ground truth, and regression-tests new versions against it. This project speaks the same language: golden ground truth plus regression detection.",
  },
  {
    id: "llm-judge",
    n: 4,
    label: "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena",
    source: "Zheng et al., NeurIPS 2023",
    url: "https://arxiv.org/abs/2306.05685",
    note: "The canonical study of using an LLM to grade model outputs, including position and verbosity bias. Motivates running the judge at temperature 0 and, critically, calibrating it against human labels.",
  },
  {
    id: "kappa",
    n: 5,
    label: "A Coefficient of Agreement for Nominal Scales (Cohen's kappa)",
    source: "Cohen, 1960",
    url: "https://doi.org/10.1177/001316446002000104",
    note: "The chance-corrected agreement statistic used in the calibration report to prove the LLM judge actually agrees with a human, rather than assuming it does.",
  },
  {
    id: "mcnemar",
    n: 6,
    label: "Note on the sampling error of the difference between correlated proportions",
    source: "McNemar, Psychometrika 1947",
    url: "https://doi.org/10.1007/BF02295996",
    note: "The paired significance test used to show a regression between agent v1 and v2 is real, not noise, because the same cases are evaluated under both versions.",
  },
  {
    id: "taubench",
    n: 7,
    label: "tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains",
    source: "Yao et al. (Sierra Research), 2024",
    url: "https://arxiv.org/abs/2406.12045",
    note: "The strongest public benchmark for tool-using support agents against policy documents. The harness here is designed to also run against it (see benchmarks/), so it generalizes beyond a self-authored scenario.",
  },
  {
    id: "ragas",
    n: 8,
    label: "RAGAS: Automated Evaluation of Retrieval Augmented Generation",
    source: "Es et al., 2023",
    url: "https://arxiv.org/abs/2309.15217",
    note: "Source of the faithfulness / groundedness idea: decompose an answer into claims and check each against the retrieved context. The groundedness metric here follows that approach.",
  },
  {
    id: "abcd",
    n: 9,
    label: "Action-Based Conversations Dataset (ABCD)",
    source: "Chen et al., NAACL 2021",
    url: "https://arxiv.org/abs/2104.00783",
    note: "10k+ support dialogues with explicit policy constraints and action state tracking. A reference for designing golden cases that test policy adherence and tool actions, not just question answering.",
  },
  {
    id: "bitext",
    n: 10,
    label: "Bitext Customer Support LLM dataset",
    source: "Bitext, HuggingFace",
    url: "https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset",
    note: "Public intent-labeled support tickets used to seed realistic golden cases before hand-authoring the hard and adversarial ones.",
  },
  {
    id: "inspect",
    n: 11,
    label: "Inspect: an open-source framework for LLM evaluations",
    source: "UK AI Safety Institute",
    url: "https://inspect.aisi.org.uk/",
    note: "Reference for reproducible, sandboxed eval design (adopted by Anthropic and DeepMind). Informs treating the golden set as versioned code and gating changes on it.",
  },
  {
    id: "langchain-loop",
    n: 12,
    label: "The agent improvement loop starts with a trace",
    source: "LangChain",
    url: "https://www.langchain.com/blog/traces-start-agent-improvement-loop",
    note: "The self-learning flywheel: production escalations and failures become new eval cases. Implemented here as harvesting failures into permanent regression cases.",
  },
];

export const CITE_BY_ID: Record<string, Citation> = Object.fromEntries(
  CITATIONS.map((c) => [c.id, c]),
);
