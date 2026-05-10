# Learning to Think from Multiple Thinkers

> **Authors:** Nirmit Joshi, Roey Magen, Nathan Srebro, Nikolaos Tsilivis, Gal Vardi

- 📅 Published: 2026-04-27
- 🏷️ Categories: cs.LG, cs.AI, cs.CC
- 🔗 arXiv: https://arxiv.org/abs/2604.24737v1
- 📄 PDF: https://arxiv.org/pdf/2604.24737v1

## Abstract

We study learning with Chain-of-Thought (CoT) supervision from multiple thinkers, all of whom provide correct but possibly systematically different solutions, e.g., step-by-step solutions to math problems written by different thinkers, or step-by-step execution traces of different programs solving the same problem.
  We consider classes that are computationally easy to learn using CoT supervision from a single thinker, but hard to learn with only end-result supervision, i.e., without CoT (Joshi et al. 2025). We establish that, under cryptographic assumptions, learning can be hard from CoT supervision provided by two or a few different thinkers, in passive data-collection settings.
  On the other hand, we provide a generic computationally efficient active learning algorithm that learns with a small amount of CoT data per thinker that is completely independent of the target accuracy $\varepsilon$, a moderate number of thinkers that scales as $\log \frac{1}{\varepsilon}\log \log \frac{1}{\varepsilon}$, and sufficient passive end-result data that scales as $\frac{1}{\varepsilon}\cdot poly\log\frac{1}{\varepsilon}$.
