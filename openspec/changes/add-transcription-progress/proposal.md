# Change: Add transcription progress output

## Why
目前轉錄過程缺乏可視化進度，使用者難以判斷是否仍在運行或卡住。

## What Changes
- 在終端機輸出轉錄進度，採每 10% 顯示一次
- 轉錄完成時輸出 100% 或完成提示

## Impact
- Affected specs: transcription-progress
- Affected code: transcription pipeline logging (transcriber / processing runner)
