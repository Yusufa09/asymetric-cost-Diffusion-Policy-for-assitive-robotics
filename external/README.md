# external/ — third-party code

Two different policies live here. **Read this before adding a repo.**

## Diffusion Policy — VENDORED (committed to this repo)

`diffusion_policy/` is a full copy of the upstream source, committed here rather
than gitignored.

| | |
|---|---|
| Upstream | https://github.com/real-stanford/diffusion_policy |
| Commit | `5ba07ac6661db573af695b419a7947ecb704690f` |
| Vendored on | 2026-07-29 |
| License | MIT — © 2023 Columbia Artificial Intelligence and Robotics Lab |
| Size | 31 MB, 369 files |

**Nothing in this tree has been modified.** It was verified clean (`git status`
empty, HEAD matching the hash above) at the moment it was vendored, and the
nested `.git` directory was removed so git stores it as ordinary files rather
than as a gitlink/submodule. **If you ever need to change DP behaviour, do it in
`src/` by wrapping or subclassing — never by editing this tree.** A local edit
here is invisible in review, unattributable to you, and destroys the guarantee
that this is upstream code at a known commit.

MIT permits redistribution provided the copyright notice ships with it;
`diffusion_policy/LICENSE` is included and must stay.

**Why vendored rather than pinned-by-hash:** a recorded hash is only a *reference*
— if upstream is deleted or force-pushed, the reference dies and the project
stops being reproducible. Experiments run until January 2027 and the fair is in
March 2027, so the code has to survive independently of anyone else's repo.

## Everything else — GITIGNORED

`.gitignore` ignores `external/*` by default and un-ignores vendored repos one at
a time. **Do not replace that with a blanket un-ignore.** LIBERO ships ~100 GB of
demonstration data; a blanket rule would attempt to commit it. If LIBERO is ever
vendored, vendor the *code* only and add its own negation line explicitly.

Reproduce any non-vendored repo from the pinned commit in `context/SETUP.md`.
