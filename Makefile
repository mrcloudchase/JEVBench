PY ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python)
EXP ?= public-fresh

.PHONY: test build run score report

test:     ## unit tests, offline
	$(PY) -m pytest -q

build:    ## rebuild every task from its source (same window and seeds; refetches)
	for t in fedreg_type fedreg_agency arxiv_category; do $(PY) -m tdm build $$t; done

run:      ## run the experiment: new runs for anything not yet run today
	$(PY) -m tdm run $(EXP)

score:    ## runs -> scores/$(EXP).json, no API calls
	$(PY) -m tdm score $(EXP)

report:   ## scores -> reports/$(EXP).md and CSVs, no API calls
	$(PY) -m tdm report $(EXP) > /dev/null
