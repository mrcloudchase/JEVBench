# fedreg_type

**Question:** what kind of Federal Register document is this? One `choice` question with three options: rule, proposed rule, notice.

**Label:** the section the Office of the Federal Register published the document in (Rules, Proposed
Rules, Notices). It follows the issuing agency's own designation of the document.

**Source:** GovInfo's bulk XML of the daily Federal Register, the Government Publishing Office's official
channel (`www.govinfo.gov/bulkdata/FR/<year>/<month>/FR-<date>.xml`).

**Legal basis:** 1 CFR 2.6: "Any person may reproduce or republish, without restriction, any material
appearing in any regular or special edition of the Federal Register." The documents are also works of
the US Government (17 U.S.C. 105). The text is committed.

**Window:** documents **filed** September 28 – October 15, 2026, published September 29 – October 16. The
filing date is used because a document is open to public inspection from the day it is filed, and the
last evaluated model's weights were published September 27.

**Sample:** documents with a summary of at least 200 characters. 90 of each type were drawn with seed 7
from 161 rules, 98 proposed rules and 646 notices.

**State:** `{"subject": ..., "summary": ...}`. The document's ACTION line is left out. Phrases that name
the type are replaced by `[document]`:
- "final rule", "proposed rule", "notice of proposed rulemaking", "proposed regulations"
- "this rule", "this notice", "rule", "notice", and their variants

Other cues remain, such as comment deadlines and effective dates, since they are the evidence.

**Known issues:** masking every "rule" and "notice" also hides uses of the words in other senses. Some
notices announce rules, such as meeting notices about rulemakings.
