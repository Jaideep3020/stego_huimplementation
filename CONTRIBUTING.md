# Working on this implementation

Use Python 3.14 and install `requirements.txt` in a virtual environment. Start with the clone/setup instructions in `docs/CLONE_AND_RUN.md`.

1. Pull the current branch before changing code.
2. Run `python run.py test`; the real-dataset integration check skips when local CT arrays are absent.
3. Keep the fixed paper configuration explicit. Changes to thresholds, kernels, order, connectivity or metric definitions require updated methodology documentation and newly measured results.
4. With the original CT input available, run `python run.py all` to audit, evaluate, visualize and verify changes.
5. Check `git diff --check` and review the changed files before committing.

Keep raw DICOM data, GT image files, generated arrays, visualizations and ZIP exports out of Git. The existing ignore rules cover them. Compact measured CSV/JSON results can be updated after a complete evaluation, with the corresponding configuration and source fingerprints.

GitHub Actions runs the unit suite on Linux, Windows and macOS. It does not download or evaluate the dataset. Never report new Dice or mIoU values unless they were measured on the recorded inputs.
