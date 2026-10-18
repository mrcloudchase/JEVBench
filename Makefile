PY ?= python

.PHONY: test data beliefs scores decisions-offline decisions-live

test:              ## unit tests, offline
	$(PY) -m pytest -q

data:              ## rebuild datasets/*/dataset.jsonl and manifest.jsonl from the live sources (a new sample)
	for d in steam_recommend appstore_stars appstore_app; do $(PY) datasets/$$d/wrangle.py; done

beliefs:           ## every provider on every dataset, then scores (resumes; cached)
	$(PY) experiments/beliefs.py

scores:            ## re-score the committed belief results, no calls
	$(PY) experiments/beliefs.py --score

decisions-offline: ## E1-E5 over the recorded beliefs, no calls
	$(PY) experiments/decisions_offline.py

decisions-live:    ## E6-E7 on TypeSafe and OpenAI, then score
	$(PY) experiments/decisions_live.py && $(PY) experiments/decisions_live.py --score
