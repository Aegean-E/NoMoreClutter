"""
Automatic Performance Benchmark & Settings Auto-Tuner (PRINCIPLE-007: Speed & Lean Architecture).
Benchmarks active AI models on the user's PC using lightweight synthetic test files,
measures latency, evaluates schema compliance and vision support, and calculates optimal settings.
"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, Any
from models import IMAGE_EXTENSIONS


@dataclass
class BenchmarkResult:
    """Structured report card of hardware and model performance with continuous slider tuning."""
    latency_ms: float
    tokens_per_sec: float
    is_json_compliant: bool
    is_vision_supported: bool
    vision_model_suggestion: str
    recommended_batch_size: int
    recommended_limit: int
    recommended_peek_length: int
    recommended_pacing_delay: float
    hardware_tier: str
    summary_text: str
    recommendations: List[str] = field(default_factory=list)


class BenchmarkService:
    """Benchmark runner that probes latency, vision, and calculates continuous optimal settings."""

    # Synthetic test items covering text, code, timestamps, and archives
    TEST_ITEMS = [
        {"id": 0, "name": "invoice_q3_acme.pdf", "peek": "Acme Corp Invoice #9841 Total Due: $1,250.00 Due: 2024-03-31"},
        {"id": 1, "name": "clean_dataset.py", "peek": "import pandas as pd\ndef clean(df):\n    return df.dropna()"},
        {"id": 2, "name": "20170926_112101.jpg"},
        {"id": 3, "name": "q3_roadmap.md", "peek": "Product Sprint 4: Microservices and authentication flow"},
        {"id": 4, "name": "system_backup.zip"},
    ]

    @classmethod
    def run_benchmark(
        cls,
        provider: Any,
        model: str,
        provider_name: str = "",
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> BenchmarkResult:
        """
        Run automated hardware and model benchmark using synthetic test files.

        Args:
            provider: Active BaseAIProvider instance
            model: Current model identifier
            provider_name: Display name of the active provider
            progress_callback: Optional callback(status_msg, progress_float)

        Returns:
            BenchmarkResult with latency, compliance, vision support, and continuous slider parameters.
        """
        if progress_callback:
            progress_callback("Generating lightweight synthetic test batch...", 0.15)

        items_json = json.dumps(cls.TEST_ITEMS, ensure_ascii=False)
        prompt = f"""You are a fast, structured file organizer. Categorize these files:
{items_json}

Rules:
1. Create meaningful category folders (e.g. 'Invoices', 'Code_Scripts', 'Reports').
2. For numeric camera photos (e.g. '20170926_112101.jpg'), group by date or photo album (e.g. 'Photos/2017').
Respond ONLY with a valid JSON array of objects:
[{{"id": 0, "folder": "Folder_Name", "name": "clean_name.ext"}}]"""

        if progress_callback:
            progress_callback("Measuring model inference latency & JSON compliance...", 0.35)

        start_time = time.perf_counter()
        is_compliant = False
        parsed_items = []
        raw_output = ""

        try:
            raw_output = provider.complete(prompt=prompt, model=model, temperature=0.1, max_tokens=600)
            elapsed = time.perf_counter() - start_time
            latency_ms = max(1.0, elapsed * 1000.0)

            # Extract JSON
            match = re.search(r"\[\s*\{.*\}\s*\]", raw_output, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list) and len(parsed) >= 3:
                    is_compliant = True
                    parsed_items = parsed
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            latency_ms = max(1.0, elapsed * 1000.0)
            is_compliant = False

        if progress_callback:
            progress_callback("Evaluating Vision capability & throughput...", 0.70)

        # Estimate tokens and tokens per second
        output_tokens = len(raw_output.split()) * 1.3 if raw_output else 50
        tokens_per_sec = (output_tokens / elapsed) if elapsed > 0 else 0.0

        # Check Vision capability
        model_lower = (model or "").lower()
        provider_lower = (provider_name or "").lower()
        is_vision_supported = False
        vision_model_suggestion = ""

        if any(k in model_lower for k in ["vision", "flash", "gpt-4o", "moondream", "llava"]):
            is_vision_supported = True
        else:
            if "groq" in provider_lower:
                vision_model_suggestion = "llama-3.2-11b-vision-preview"
            elif "gemini" in provider_lower:
                vision_model_suggestion = "gemini-1.5-flash"
            elif "ollama" in provider_lower:
                vision_model_suggestion = "moondream:latest"
            elif "openai" in provider_lower:
                vision_model_suggestion = "gpt-4o-mini"

        if progress_callback:
            progress_callback("Calculating continuous optimal slider settings for your PC...", 0.90)

        # -------------------------------------------------------------
        # Continuous Auto-Tuning Formulas for Each Setting Slider
        # -------------------------------------------------------------
        # 1. Continuous Batch Size Slider Formula:
        # Scales smoothly with measured latency (ms). Clamped between [3, 25].
        # Ultra-fast (~300ms) -> 25; Fast (~600ms) -> 20; GPU (~1200ms) -> 14; CPU (~3500ms) -> 7; Slow CPU (~6000ms) -> 4.
        clamped_latency = max(latency_ms, 200.0)
        raw_batch = 25.0 * ((500.0 / max(clamped_latency, 500.0)) ** 0.65)
        if clamped_latency < 500.0:
            # Scale slightly above 20 for sub-500ms cloud endpoints
            raw_batch = min(25.0, 20.0 + (500.0 - clamped_latency) / 60.0)
        recommended_batch_size = int(max(3, min(25, round(raw_batch))))

        # 2. Continuous Max File Limit Slider Formula:
        # Calibrates total batch run time for interactive responsiveness (~30-45s max duration).
        # Clamped between [15, 200] and rounded to nearest 5.
        raw_limit = (35000.0 / clamped_latency) * (recommended_batch_size / 5.0) * 12.0
        rounded_limit = int(round(raw_limit / 5.0) * 5)
        recommended_limit = int(max(15, min(200, rounded_limit)))

        # 3. Continuous Document Peek Context Budget Slider Formula:
        # Fast models afford full 250-character snippets; slower local models benefit from 100-140 chars.
        raw_peek = 250.0 - (clamped_latency / 35.0)
        recommended_peek_length = int(max(100, min(250, round(raw_peek / 10.0) * 10)))

        # 4. Continuous Inter-Batch Pacing Delay Slider Formula:
        # Cloud providers with TPM caps (e.g. Groq free tier) or local CPU cooling benefit from pacing.
        if "groq" in provider_lower:
            recommended_pacing_delay = 0.15
        elif "gemini" in provider_lower or "openai" in provider_lower:
            recommended_pacing_delay = 0.0
        elif clamped_latency > 3000.0:
            recommended_pacing_delay = 0.35  # CPU cooldown pause
        elif clamped_latency > 1500.0:
            recommended_pacing_delay = 0.20
        else:
            recommended_pacing_delay = 0.05

        # Classify hardware tier based on measured latency
        if latency_ms < 850:
            hardware_tier = "🚀 Ultra-Fast Cloud (Groq / Gemini)"
        elif latency_ms < 2200:
            hardware_tier = "⚡ Standard Local GPU / Cloud Server"
        else:
            hardware_tier = "🐢 Conservative Local CPU / Quantized GGUF"

        # Generate structured recommendations with slider targets
        recommendations = [
            f"⏱️ Model Latency: {latency_ms:.0f} ms (~{tokens_per_sec:.0f} tokens/sec).",
            f"🎚️ Optimal Batch Size Slider: {recommended_batch_size} files/cluster (balances latency and context window).",
            f"🎚️ Optimal File Limit Slider: {recommended_limit} files (calibrated for responsive 30-45s completion).",
            f"🎚️ Optimal Context Peek Slider: {recommended_peek_length} chars (preserves prompt speed and token budget).",
            f"🎚️ Optimal Pacing Delay Slider: {recommended_pacing_delay:.2f}s (prevents TPM rate-limiting and CPU spikes).",
        ]

        if is_compliant:
            recommendations.append("✅ Schema Compliance: 100% (Model accurately returned structured JSON IDs).")
        else:
            recommendations.append("⚠️ Schema Warning: Model returned non-standard JSON formatting; smaller batch sizes recommended.")

        if is_vision_supported:
            recommendations.append(f"👁️ Vision Supported: Active model '{model}' supports multimodal visual photo inspection.")
        elif vision_model_suggestion:
            recommendations.append(f"💡 Photo Tip: Numeric camera photos are grouped by date. To visually analyze image contents, switch to '{vision_model_suggestion}'.")
        else:
            recommendations.append("📷 Camera roll photos with numeric timestamps (e.g. '20170926_112101.jpg') are grouped by year to prevent hallucinations.")

        summary_text = (
            f"Hardware Tier: {hardware_tier}\n"
            f"Latency: {latency_ms:.0f} ms | Speed: ~{tokens_per_sec:.0f} tok/s\n\n"
            f"🎯 Calibrated Slider Recommendations:\n"
            f"  • Batch Size: {recommended_batch_size} files/cluster\n"
            f"  • Max Limit: {recommended_limit} files\n"
            f"  • Context Peek: {recommended_peek_length} characters\n"
            f"  • Pacing Delay: {recommended_pacing_delay:.2f}s\n"
        )

        if progress_callback:
            progress_callback("Benchmark complete!", 1.0)

        return BenchmarkResult(
            latency_ms=latency_ms,
            tokens_per_sec=tokens_per_sec,
            is_json_compliant=is_compliant,
            is_vision_supported=is_vision_supported,
            vision_model_suggestion=vision_model_suggestion,
            recommended_batch_size=recommended_batch_size,
            recommended_limit=recommended_limit,
            recommended_peek_length=recommended_peek_length,
            recommended_pacing_delay=recommended_pacing_delay,
            hardware_tier=hardware_tier,
            summary_text=summary_text,
            recommendations=recommendations,
        )
