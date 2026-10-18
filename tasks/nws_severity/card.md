# nws_severity

**Question:** how severe a threat to life or property does this weather alert describe? One `score` question with four ordered levels, Minor < Moderate < Severe < Extreme, each with its CAP definition.

**Label:** the alert's CAP `severity` as issued by the National Weather Service, as a level index 0–3.

**Source:** api.weather.gov `/alerts`, first issuances (`message_type=alert`, `status=actual`) held by the API on October 18, 2026, covering alerts sent October 11–19. Pages are cached in `tasks/.sources/nws/`. The API keeps seven days, so a later rebuild draws newer alerts.

**Legal basis:** NWS web pages and data "are in the public domain, unless specifically noted otherwise" and may be used "without charge for any lawful purpose" ([NWS disclaimer](https://www.weather.gov/disclaimer)). The API is "intended to be open data, free to use for any purpose" ([API documentation](https://www.weather.gov/documentation/services-web-api)). As the conditions require: this is text from U.S. National Weather Service alerts and is not subject to copyright; it is not an official NWS product, and NWS does not endorse this work. The text is committed.

**Contamination:** every alert was issued after the last evaluated model was published (September 27).

**Sample:** one record per distinct description (an alert reissued for several zones counts once). Up to
100 per level with seed 7: 100 Minor, 100 Moderate, 100 Severe and all 16 Extreme. 35 event types.

**State:** `{"description": ..., "instruction": ...}`. The event name, headline and area are left out.

**Known issues:** NWS assigns severity largely by product type (a Gale Warning is Severe, a Small Craft
Advisory Minor), so the task partly tests recognizing the product from the hazard described. Extreme is
rare (16 records), so per-level results for it are noisy. Near-duplicate texts from the same storm can occur.
