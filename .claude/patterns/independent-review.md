# PAT-003 — Independent Review

The reviewer receives the artifact and approved brief, but not the producer's private reasoning. For puzzles, verification is code-driven: a separate solver independently re-derives uniqueness, solvability, answer keys, and difficulty accuracy from the seed — it does not re-use the generator's own answers. It records findings without editing the source. A separate revision pass applies accepted changes. A new verification pass checks each acceptance condition against the revised hash.
