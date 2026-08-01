# Evaluating Multi-Turn Multimodal Diagnostic Reasoning on Challenging Real-World Clinical Cases

> **Authors:** Rui Yang, Weihao Xuan, Yi Lin, Zhuhan Bao, Jonathan Chong Kai Liew et al. (26 authors total)

- 📅 Published: 2026-07-28
- 🏷️ Categories: cs.CL, cs.AI
- 🔗 arXiv: https://arxiv.org/abs/2607.25933v1
- 📄 PDF: https://arxiv.org/pdf/2607.25933v1

## Abstract

Clinical diagnostic evaluation should not only assess whether models can provide correct diagnoses, but also reflect the realities of clinical practice, including progressive disclosure of multimodal information, dynamic updating of diagnostic hypotheses, and continuous refinement of clinical reasoning. However, existing evaluations of multimodal large language models (MLLMs) typically rely on single-turn or isolated tasks, making it difficult to fully capture the complexity of real-world clinical diagnosis. To bridge this gap, we developed ClinMM-Bench, the largest multi-turn multimodal clinical diagnostic evaluation benchmark to date. ClinMM-Bench contains 1,089 challenging real-world clinical cases and 3,760 medical images across eight specialties. We systematically evaluated 15 representative MLLMs using a two-level evaluation framework that assessed both diagnostic accuracy and diagnostic reasoning quality. Results showed that proprietary models achieved the highest overall diagnostic accuracy, but the proportion of completely correct diagnoses remained limited across all models. In terms of diagnostic reasoning quality, current models can identify plausible diagnostic directions but still have considerable limitations in generating reliable diagnostic reasoning. Error analysis further identified five representative failure modes: information synthesis failure, knowledge mapping error, perception error, premature closure, and visual hallucination.
