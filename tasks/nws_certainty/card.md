# nws_certainty

**Question:** how certain is it that the hazard described in this weather alert occurs? One `score` question with three ordered levels, Possible < Likely < Observed, each with its CAP definition.

**Label:** the alert's CAP `certainty` as issued by the National Weather Service, as a level index 0–2.

**Source:** api.weather.gov `/alerts`, first issuances (`message_type=alert`, `status=actual`) held by the API on October 18, 2026, covering alerts sent October 11–19. Pages are cached in `tasks/.sources/nws/`. The API keeps seven days, so a later rebuild draws newer alerts.

**Legal basis:** NWS web pages and data "are in the public domain, unless specifically noted otherwise" and may be used "without charge for any lawful purpose" ([NWS disclaimer](https://www.weather.gov/disclaimer)). The API is "intended to be open data, free to use for any purpose" ([API documentation](https://www.weather.gov/documentation/services-web-api)). As the conditions require: this is text from U.S. National Weather Service alerts and is not subject to copyright; it is not an official NWS product, and NWS does not endorse this work. The text is committed.

**Contamination:** every alert was issued after the last evaluated model was published (September 27).

**Sample:** one record per distinct description; 100 per level with seed 7. 34 event types.

**State:** `{"description": ..., "instruction": ...}`. The event name, headline and area are left out.

**Known issues:** watches are mostly Possible and radar-based warnings are often Observed, so product type is
a strong cue. "Likely" covers most forecasts and is the hardest level to separate.
