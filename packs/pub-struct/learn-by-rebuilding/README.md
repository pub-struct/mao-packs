# Learn by rebuilding

Learn one concept by rebuilding the smallest version of it from scratch, explaining it
out loud, and shipping both. It is the loop Andrej Karpathy has run in public for years
(CS231n, micrograd, nanoGPT, nanochat), set up as three agents and the notes they share:

* **Builder** rebuilds the concept one runnable step at a time, with no library that hides
  the part being learned, and logs every step with the command to run it.
* **Student** runs every step, says what it thinks the code does, and asks about every
  word that was not explained. Its questions are the map of where people get lost.
* **Explainer** turns the Build log and the Student's questions into a lecture script to
  record from a blank screen, and a post about the part that surprised you.

When you add an arrangement, MAO asks for the concept (attention, embeddings, RAG, an
agent loop...) and the language and libraries the toy version may use.

## Arrangements

* **Four weekends**: the Builder, the Student and the Explainer, wired to each other and
  to the Concept brief, Build log, Lecture script and Post draft notes. The brief holds the
  four-weekend checklist: pick, rebuild, explain, ship.
* **Weekend sprint**: only the Builder and the Student, with the brief and the Build log,
  for a single concept in a single weekend.

## Agents and roles

The three roles are reusable on any agent (`mao role show pub-struct/builder`), and the
pack's agents recruit one of each on Claude Code
(`mao recruit Builder --preset pub-struct/builder`). Nothing in this pack runs a custom
command, so it asks for no approval.
