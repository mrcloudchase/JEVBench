# fedreg_agency

**Question:** which department or agency issued this Federal Register document? One `choice` question over ten options.

**Label:** the issuing agency in the document's own header (its `AGENCY` element), grouped by cabinet
department. Component agencies count as their department: the FAA as Transportation, the FDA as Health and Human Services.

**Source, legal basis and window:** as for [`fedreg_type`](../fedreg_type/card.md): GovInfo bulk XML,
1 CFR 2.6, filed September 28 – October 15, 2026.

**Sample:** documents with a summary of at least 200 characters, from the ten agencies with the most
documents in the window. 30 per agency with seed 7; Defense had only 26. The set holds 200 notices, 55
rules and 41 proposed rules.

**State:** `{"subject": ..., "summary": ...}`. The names and acronyms of all ten agencies and their
listed components are replaced by `[agency]` in **every** document alike, so the masking itself carries no
clue. This covers "Department of X" and "Secretary of X", plus each document's own sub-agency. Topic
words such as "airworthiness" or "fishery" remain: inferring the agency from them is the task.

**Known issues:** the number of `[agency]` tokens varies by agency (0.9 to 4.3 per record on average),
which is a weak cue. A few documents name other agencies (Education, Agriculture, state departments),
which is ordinary context.
