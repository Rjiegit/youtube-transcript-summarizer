## ADDED Requirements

### Requirement: Use weighted Gemini model selection
The system SHALL select a Gemini model per request using weighted random selection among a code-defined set of Gemini model identifiers and weights.

#### Scenario: Valid configuration is provided
- **GIVEN** the weighted model list contains `gemini-2.5-flash (5)`, `gemini-3-flash (5)`, and `gemini-2.5-flash-lite (10)`
- **WHEN** the summarizer uses the Gemini backend
- **THEN** it selects a Gemini model per request using weighted random selection

#### Scenario: Weighted list is empty
- **GIVEN** the weighted model list is empty (or invalid)
- **WHEN** the summarizer uses the Gemini backend
- **THEN** it uses the existing default Gemini model configuration

### Requirement: Record selected Gemini model label
When the Gemini backend is used, the system SHALL record the selected Gemini model identifier for downstream persistence/observability (e.g., `last_model_label` and stored `model_label`).

#### Scenario: Model label reflects the selected model
- **GIVEN** the summarizer selects `gemini-2.5-flash-lite`
- **WHEN** processing persists the summary metadata
- **THEN** the stored model label includes `gemini-2.5-flash-lite`

### Requirement: Graceful fallback on invalid weights
If the weighted model list is invalid (e.g., total weight is not positive), the system SHALL fall back to the default Gemini model.

#### Scenario: Invalid configuration falls back
- **GIVEN** the weighted model list contains no valid positive weights
- **WHEN** the summarizer uses the Gemini backend
- **THEN** it falls back to the existing default Gemini model configuration
