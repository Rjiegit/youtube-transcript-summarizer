# transcription-progress Specification

## Purpose
定義轉錄期間依音訊時間軸以固定里程碑輸出進度，讓終端使用者能掌握長音訊處理狀態，並規範無法取得總長度或進度跨越多個里程碑時的行為。
## Requirements
### Requirement: Transcription progress output
The system SHALL output transcription progress to the terminal at 10% increments while generating a transcript.

#### Scenario: Progress updates during transcription
- **WHEN** a transcription job is running
- **THEN** the terminal displays progress updates at 10% milestones until completion
