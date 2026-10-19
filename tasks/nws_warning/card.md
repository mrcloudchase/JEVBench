# nws_warning

**Question:** is this weather alert a warning? One `noul` question, with criteria describing warnings against advisories, watches and statements.

**Label:** 1 when the National Weather Service issued the alert as a Warning (its event name ends in
"Warning"), 0 for advisories, watches and statements.

**Source:** api.weather.gov `/alerts`, first issuances (`message_type=alert`, `status=actual`) held by the API on October 18, 2026, covering alerts sent October 11–19. Pages are cached in `tasks/.sources/nws/`. The API keeps seven days, so a later rebuild draws newer alerts.

**Legal basis:** NWS web pages and data "are in the public domain, unless specifically noted otherwise" and may be used "without charge for any lawful purpose" ([NWS disclaimer](https://www.weather.gov/disclaimer)). The API is "intended to be open data, free to use for any purpose" ([API documentation](https://www.weather.gov/documentation/services-web-api)). As the conditions require: this is text from U.S. National Weather Service alerts and is not subject to copyright; it is not an official NWS product, and NWS does not endorse this work. The text is committed.

**Contamination:** every alert was issued after the last evaluated model was published (September 27).

**Sample:** one record per distinct description; 500 warnings and 500 others with seed 7. 43 event types.

**State:** `{"description": ..., "instruction": ...}` with the words warning, watch, advisory and statement
masked as `[alert]`; the event name, headline and area are left out.

**Known issues:** some hazards have both a warning and an advisory (Freeze Warning, Frost Advisory); telling
them apart from the description alone is the task.
