PY ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python)
EXP ?= fresh-reviews

.PHONY: test build run score report

test:     ## unit tests, offline
	$(PY) -m pytest -q

build:    ## rebuild every task from its source (draws a new sample: a new task version)
	for t in steam_recommend appstore_stars appstore_app; do $(PY) -m tdm build $$t; done

run:      ## run the experiment: new runs for anything not yet run today
	$(PY) -m tdm run $(EXP)

score:    ## runs -> scores/$(EXP).json, no API calls
	$(PY) -m tdm score $(EXP)

report:   ## scores -> reports/$(EXP).md and CSVs, no API calls
	$(PY) -m tdm report $(EXP) > /dev/null
