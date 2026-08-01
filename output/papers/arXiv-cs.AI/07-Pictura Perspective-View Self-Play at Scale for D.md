# Pictura: Perspective-View Self-Play at Scale for Driving

> **Authors:** Yuan Yin, Elias Ramzi, Marc Lafon, Valentin Charraut, Victor Bares et al. (11 authors total)

- 📅 Published: 2026-07-28
- 🏷️ Categories: cs.CV, cs.AI, cs.RO
- 🔗 arXiv: https://arxiv.org/abs/2607.26005v1
- 📄 PDF: https://arxiv.org/pdf/2607.26005v1

## Abstract

Self-play in simulation produces robust driving policies at scale. Demonstrations of such behavior have been made using privileged vectorized observations such as exact poses and velocities, even for occluded agents. This assumes that perception is solved and introduces a representation gap with the partial observation of a deployed agent driving from the perspective view of egocentric cameras. A common fix, distilling the privileged policy into a camera-input student, leaves the student imitating decisions its own view cannot justify. Instead, we establish perspective-view self-play as a practical training regime. We introduce Pictura, a GPU-accelerated multi-agent driving simulator that renders each agent's egocentric view at every step, mitigating the representation gap at its source. Pictura sustains up to 500K agent-steps/s (2M images/s) on a single H100. Using Pictura, we train Alberti by self-play with plain PPO. It is the first large-scale driving self-play policy trained directly from perspective images, without privileged observations. Training spans 50B agent steps for ~35M km of driving. It approaches the driving performance of its privileged vectorized counterpart, and transfers zero-shot to Waymo Open Motion Dataset layouts re-rendered in Pictura, where it outperforms privileged vectorized agents. Project page: https://valeoai.github.io/Pictura/
