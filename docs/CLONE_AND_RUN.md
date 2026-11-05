# Clone and continue on another PC

The Git repository contains the code, fixed configuration, tests, methodology notes and compact measured results. Original CT data, generated NumPy caches, PNG images and ZIP exports are excluded from Git. Copy the CT input once on each machine; all output images and arrays are reproducible from it.

## 1. Clone and open

```sh
git clone https://github.com/Jaideep3020/stego_huimplementation.git
cd stego_huimplementation
```

Open this folder in VS Code, or open `STEGO_IMPLEMENTATION_USINGHU.code-workspace`. All workspace paths are relative.

## 2. Create a Python environment

Use Python 3.14 (the recorded run used 3.14.5).

Windows PowerShell, without requiring virtual-environment activation:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS / Linux:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Choose this `.venv` interpreter in VS Code. Dependency versions are pinned. The full dataset evaluation has been executed on macOS. The dataset-independent test suite also passed GitHub Actions on Windows, Linux and macOS; the complete CT evaluation has not been run on those other platforms. The Python runner avoids Make, shell activation and hardcoded temporary-directory paths.

## 3. Copy the dataset

Copy the existing local `CT` directory with all patient folders into:

```text
DATASET/CHAOS_Train_Sets/Train_Sets/CT/
  1/
    DICOM_anon/
    Ground/
  ...other patients...
```

Use the same original DICOM and matching ground-truth files to reproduce the recorded results. Keep the patient directory names. Do not substitute MRI or windowed JPEG/PNG scans for raw CT DICOM. The first audit checks counts, labels, HU tags and source fingerprints.

Alternatively, keep CT outside the project and pass its location:

```powershell
.\.venv\Scripts\python.exe run.py all --data "D:\CHAOS\CT" --workers 6
```

```sh
.venv/bin/python run.py all --data /path/to/CT --workers 6
```

The CT directory and masks are not supplied by `git clone`. They can be copied directly from the original PC or obtained separately from the dataset provider, subject to its terms. Several GB of local disk space are used by regenerated arrays.

## 4. Reproduce scores and visualizations

Windows:

```powershell
.\.venv\Scripts\python.exe run.py all --workers 6
```

macOS / Linux:

```sh
.venv/bin/python run.py all --workers 6
```

This runs the CT audit, tests, fixed paper evaluation, dataset plots, stage figure, patient exports, original-data integrity check, deterministic rerun and report. No additional experiment or parameter tuning is performed.

Individual steps also work, for example:

```sh
python run.py test
python run.py evaluate
python run.py visualization --archive
python run.py report
```

These shorter commands assume the intended virtual environment is active. Outputs are `reports/paper_protocol/`, `reports/REPRODUCTION_REPORT.md` and `visualization/CT_<patient>/`.

## 5. Continue work

Before changing code on the other machine, run `git pull`. Configure the commit author on that machine if needed:

```sh
git config user.name "Your name"
git config user.email "Your commit email"
```

Authenticate the local Git client with GitHub before pushing. The GitHub connection inside Codex does not automatically configure terminal credentials on another PC.

 After making and testing changes, commit and push your source/configuration changes. Generated arrays and images stay local. Copying the same data and using the fixed configuration is essential; changing a dataset, kernel or threshold can change the results.
