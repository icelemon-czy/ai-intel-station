# Personalized Worked Example Generation from Student Code Submissions using Pattern-based Knowledge Components

> **Authors:** Griffin Pitts, Muntasir Hoq, Peter Brusilovsky, Narges Norouzi, Arto Hellas et al. (7 authors total)

- 📅 Published: 2026-04-27
- 🏷️ Categories: cs.HC, cs.AI, cs.CY
- 🔗 arXiv: https://arxiv.org/abs/2604.24758v1
- 📄 PDF: https://arxiv.org/pdf/2604.24758v1

## Abstract

Adaptive programming practice often relies on fixed libraries of worked examples and practice problems, which require substantial authoring effort and may not correspond well to the logical errors and partial solutions students produce while writing code. As a result, students may receive learning content that does not directly address the concepts they are working to understand, while instructors must either invest additional effort in expanding content libraries or accept a coarse level of personalization. We present an approach for knowledge-component (KC) guided educational content generation using pattern-based KCs extracted from student code. Given a problem statement and student submissions, our pipeline extracts recurring structural KC patterns from students' code through AST-based analysis and uses them to condition a generative model. In this study, we apply this approach to worked example generation, and compare baseline and KC-conditioned outputs through expert evaluation. Results suggest that KC-conditioned generation improves topical focus and relevance to learners' underlying logical errors, providing evidence that KC-based steering of generative models can support personalized learning at scale.
