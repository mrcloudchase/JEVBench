# Local model servers

Three open models run on this machine and speak the System One wire format, so `tdm.providers`
reaches them like any hosted provider (`von`, `opendecider`, `openjev`). None needs a key.

```bash
pip install -e ".[local]"                                   # torch, transformers, von-sdk, opendecider[serve]
von serve --port 8101 --device cpu --noul-decision raw      # raw: the posterior, not Von's abstention band
opendecider serve --port 8102 --device cpu --request-timeout-s 300
python servers/openjev.py --port 8103                       # open-jev ships no server; this is one
```

| Provider | Model | Weights | Port |
|---|---|---|---|
| `von` | Von 1.3, 395M ModernBERT (wfzyx/von, Apache-2.0) | September 24, 2026 | 8101 |
| `opendecider` | OpenDecider nano, ~0.4B (manjunathshiva/opendecider-nano) | September 27, 2026 | 8102 |
| `openjev` | open-jev-deberta-v3-large, 0.4B (com-kotobalabs, Apache-2.0) | September 18, 2026 | 8103 |

On the paper's 4-CPU machine, a record took about 0.5 s (OpenDecider), 1 s (open-jev) and 1–2.5 s
(Von). `openjev.py` sends an option's criteria description as its text and structured states as JSON;
the model truncates states to 256 tokens.
