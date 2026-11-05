PYTHON ?= python3
WORKERS ?= 6
export MPLCONFIGDIR := /tmp/liver-hu-matplotlib
export OPENBLAS_NUM_THREADS := 1
export OMP_NUM_THREADS := 1

.PHONY: all audit test evaluate figures diagnostics visualization export integrity verify report
all:
	$(MAKE) audit
	$(MAKE) test
	$(MAKE) evaluate
	$(MAKE) diagnostics
	$(MAKE) figures
	$(MAKE) visualization
	$(MAKE) integrity
	$(MAKE) verify
	$(MAKE) report

audit:
	$(PYTHON) -m src.io_chaos

test:
	$(PYTHON) -m unittest discover -s tests -v

evaluate:
	$(PYTHON) -m src.run_experiment --workers $(WORKERS)

diagnostics:
	$(PYTHON) -m src.diagnostics

figures:
	$(PYTHON) -m src.make_figures

visualization:
	$(PYTHON) -m src.export_segmentations --out visualization --no-archive --workers $(WORKERS)

export:
	$(PYTHON) -m src.export_segmentations --out visualization --workers $(WORKERS)

integrity:
	$(PYTHON) -m src.check_integrity --workers $(WORKERS)

verify:
	$(PYTHON) -m src.verify --workers $(WORKERS)

report:
	$(PYTHON) -m src.report
