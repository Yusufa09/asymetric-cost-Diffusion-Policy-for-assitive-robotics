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

## LIBERO — VENDORED (committed to this repo)

`LIBERO/` is a full copy of the upstream source, committed here rather than
gitignored. Same policy and same reasoning as Diffusion Policy above.

| | |
|---|---|
| Upstream | https://github.com/Lifelong-Robot-Learning/LIBERO |
| Commit | `8f1084e3132a39270c3a13ebe37270a43ece2a01` (2025-03-15) |
| Vendored on | 2026-08-02 |
| License | MIT — © 2023 Lifelong Robot Learning |
| Size | **426 MB, 1116 files** |

Verified clean (`git status` empty, HEAD matching) before the nested `.git` was
removed. **Nothing in this tree has been modified**, and nothing may be — wrap or
subclass from `src/`.

**Why 426 MB and not 22 MB.** 404 MB of it is `libero/libero/assets` — MuJoCo
meshes and textures. Those are as load-bearing as the Python: without them the sim
does not run, so the "vendor the code only" rule below means *not the demo
datasets*, not *not the assets*. The survival argument that justifies vendoring at
all applies to assets identically — if upstream disappears, missing meshes break
reproduction exactly as thoroughly as missing code.

**The datasets are NOT here and must never be.** The ~100 GB of demonstration
HDF5 lands in `LIBERO/libero/datasets/` when `download_libero_datasets.py` runs.
Two guards: LIBERO's own nested `.gitignore` ignores `datasets`, and the top-level
`.gitignore` has an explicit `external/LIBERO/libero/datasets/` line. **The second
one is the one that matters** — the first is a third-party file we do not control.
Demo data belongs on the GPU instance.

## Everything else — GITIGNORED

`.gitignore` ignores `external/*` by default and un-ignores vendored repos one at
a time. **Do not replace that with a blanket un-ignore.**

Reproduce any non-vendored repo from the pinned commit in `context/SETUP.md`.

## Two traps, both hit for real

1. **Delete the nested `.git` before staging.** Otherwise git records a **gitlink
   (mode 160000)** — an accidental submodule, the exact thing this policy rejects.
   Verify with `git ls-files -s external/<repo> | awk '$1=="160000"'`; it must
   print nothing.
2. **Diff files-on-disk against files-staged after vendoring.** On 2026-08-02 the
   top-level `.gitignore` rule `data/` — unanchored, so matching a directory named
   `data` at *any* depth — silently dropped
   `LIBERO/libero/configs/data/default.yaml`, the file defining observation
   modalities and `obs_key_mapping`. Fixed by anchoring the rule to `/data/`. A
   vendored tree missing one file looks identical to a complete one until it
   breaks months later.

   ```bash
   comm -23 <(find external/<repo> -type f | sort) <(git ls-files external/<repo> | sort)
   ```

   Expect `__pycache__/*.pyc` to be absent — that is correct and intended. Anything
   else in that output is a bug.
