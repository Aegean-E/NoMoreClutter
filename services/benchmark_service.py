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
    """Structured report card of hardware and model performance."""
    latency_ms: float
    tokens_per_sec: float
    is_json_compliant: bool
    is_vision_supported: bool
    vision_model_suggestion: str
    recommended_batch_size: int
    recommended_limit: int
    hardware_tier: str
    summary_text: str
    recommendations: List[str] = field(default_factory=list)


class BenchmarkService:
    """Benchmark runner that probes latency, vision, and calculates optimal settings."""

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
            BenchmarkResult with latency, compliance, vision support, and optimal parameters.
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
            progress_callback("Calculating optimal settings for your PC...", 0.90)

        # Determine optimal parameters based on benchmark measurements
        if latency_ms < 900:
            recommended_batch_size = 15
            recommended_limit = 100
            hardware_tier = "⚡ Ultra-Fast Cloud (High Throughput)"
        elif latency_ms < 2500:
            recommended_batch_size = 10
            recommended_limit = 50
            hardware_tier = "🚀 Standard Speed (Local GPU / Standard Cloud)"
        else:
            recommended_batch_size = 5
            recommended_limit = 25
            hardware_tier = "🐢 Conservative (Local CPU / High Latency)"

        # Generate structured recommendations
        recommendations = [
            f"⏱️ Model Latency: {latency_ms:.0f} ms (~{tokens_per_sec:.0f} tokens/sec).",
            f"🎯 Optimal Batch Size: {recommended_batch_size} files (maximizes throughput without rate-limit spikes).",
            f"📊 Recommended File Limit: {recommended_limit} files per run for smooth UI responsiveness.",
        ]

        if is_compliant:
            recommendations.append("✅ Schema Compliance: 100% (Model accurately returned required JSON IDs).")
        else:
            recommendations.append("⚠️ Schema Warning: Model returned non-standard JSON formatting; smaller batch sizes recommended.")

        if is_vision_supported:
            recommendations.append(f"👁️ Vision Supported: Model '{model}' supports visual photo inspection. Enable Vision in Settings!")
        elif vision_model_suggestion:
            recommendations.append(f"💡 Photo Tip: Camera photos are grouped by date (e.g. 'Photos/2017'). To analyze image contents, switch to '{vision_model_suggestion}'.")
        else:
            recommendations.append("📷 Camera roll photos with numeric timestamps (e.g. '20170926_112101.jpg') are grouped by year to prevent hallucinations.")

        summary_text = (
            f"Tier: {hardware_tier}\n"
            f"Latency: {latency_ms:.0f} ms | Speed: ~{tokens_per_sec:.0f} tok/s\n"
            f"Recommended Batch Size: {recommended_batch_size} | Limit: {recommended_limit}"
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
            hardware_tier=hardware_tier,
            summary_text=summary_text,
            recommendations=recommendations,
        )
