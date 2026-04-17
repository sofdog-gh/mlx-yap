# Notes & Issues

## Whisper repetition bug (hallucination loop)

Whisper sometimes gets stuck in a repetition loop, producing output like "very very very very very very…" many times. This is a known Whisper hallucination issue — likely triggered by ambient noise, silence at the end of a recording, or certain audio patterns. Needs investigation into suppression strategies (e.g. compression_ratio_threshold, no_speech_threshold, condition_on_previous_text=False, or post-hoc deduplication).

---

## Post-processing should operate on existing terminal content, not the transcription

**Current behaviour:** in cleanup/summarize/clarify mode, the voice is transcribed and the post-processing is applied to the transcription before pasting.

**Intended behaviour:** post-processing capabilities should take whatever text is already present in the terminal (e.g. what's already typed at the prompt, or a previous transcription) and process that — independently of the voice recording flow.

Needs design thought: how to capture the existing terminal content (clipboard? select-all? cursor buffer?), and how the trigger should work for this case.
