# Collaborative System Failure Prognostics via Federated Longitudinal-Survival Modeling

> **Authors:** Fan Yang, Madelyn Weller, Dimuthu Fernando, Hila Livneh, Yuxin Wen

- 📅 Published: 2026-07-28
- 🏷️ Categories: cs.LG
- 🔗 arXiv: https://arxiv.org/abs/2607.26038v1
- 📄 PDF: https://arxiv.org/pdf/2607.26038v1

## Abstract

Time-to-event modeling provides a systematic framework for estimating time-dependent failure risk, reliability, and remaining useful life (RUL) from longitudinal condition monitoring data. However, applying these models to distributed prognostics remains challenging because sensor trajectories and failure-time records are often stored across organizations or operational sites and cannot be centrally pooled due to privacy or proprietary constraints. Moreover, the classical Cox proportional hazards model relies on a nonseparable partial likelihood involving global risk sets, making direct optimization difficult under standard federated learning protocols. This paper presents a federated longitudinal-survival modeling framework for collaborative system failure prognostics. The proposed framework combines longitudinal sensor representation learning with a client-separable discrete-time hazard objective, enabling multiple clients to collaboratively train a prognostic model without sharing raw sensor measurements or individual failure records. Time-dependent representations extracted from multivariate sensor histories are used to estimate interval-specific failure hazards, reliability curves, and system RUL. Experiments on the four C-MAPSS turbofan engine degradation subsets under simulated decentralized settings demonstrate that the proposed framework consistently improves prognostic performance over isolated local training while maintaining performance comparable to centralized training across heterogeneous operating conditions and failure modes. These results demonstrate the potential of federated longitudinal-survival modeling for collaborative, data-aware condition monitoring and system failure prognostics.
