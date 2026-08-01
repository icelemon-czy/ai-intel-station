# Empirical Evaluation of Out-Of-Distribution Performance of Tabular Foundation Models

> **Authors:** Malena Loza, David Chushig-Muzo, Eva Milara, Luis Bote-Curiel, Luis Estrada-Petrocelli et al. (6 authors total)

- 📅 Published: 2026-07-28
- 🏷️ Categories: cs.LG, cs.AI
- 🔗 arXiv: https://arxiv.org/abs/2607.26000v1
- 📄 PDF: https://arxiv.org/pdf/2607.26000v1

## Abstract

Tabular Foundation Models (TFMs) have emerged as novel approaches for tabular predictive tasks, demonstrating competitive predictive performance to ensemble tree-based models. Most TFMs are trained and evaluated on independent and identically distributed data, but this assumption changes in real-world scenarios due to distribution shifts, which compromise the robustness of models. Limited research has been conducted of TFMs under distribution shifts. We present an empirical evaluation of Out-Of-Distribution (OOD) performance of nine TFMs, spanning diverse pre-training strategies and architectures: TabPFNv2, TabPFNv2.5, TabPFNv2.6, TabPFNv3, TabICL, TabICLv2, Mitra, LimiX and TabFM. Three real-world datasets from the TableShift study were considered (HELOC, Voting, Childhood Lead), covering label, socioeconomic, and geographic shift types. Our results show that all evaluated TFMs degrade systematically under distribution shift regardless of pre-training strategy, with shift gaps ranging from 0.003 to 0.060 depending on shift type. The relationship between in-distribution and OOD predictive performance documented for classical tabular models extends into TFMs. We also identified a scalability gap, as high-performing models demand significant memory and computational resources beyond what standard deployment infrastructure can support. This study extends existing benchmarks for OOD in tabular data, providing evidence to support their adoption in high-stakes domains characterized by structural distribution shifts.
