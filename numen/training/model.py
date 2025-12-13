"""
Numen model architecture - neuro-symbolic hybrid.

Combines neural intuition (base LLM) with symbolic verification (SymPy).
"""

from typing import Optional, Dict, Any, List
import torch
import torch.nn as nn
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, TaskType


class NumenModel:
    """
    Numen mathematical reasoning model.

    Architecture:
    - Base: DeepSeek-Math or Llama 3.1 70B
    - Fine-tuning: LoRA for efficiency
    - Integration: Symbolic verification layer
    """

    def __init__(
        self,
        base_model: str = "deepseek-ai/deepseek-math-7b-base",
        use_quantization: bool = True,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
    ):
        """
        Initialize Numen model.

        Args:
            base_model: HuggingFace model identifier
            use_quantization: Use 4-bit quantization for efficiency
            lora_r: LoRA rank
            lora_alpha: LoRA alpha parameter
            lora_dropout: LoRA dropout
        """
        self.base_model_name = base_model
        self.use_quantization = use_quantization

        # Quantization config (for large models)
        self.bnb_config = None
        if use_quantization:
            self.bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )

        # LoRA config
        self.lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # Attention layers
            bias="none",
        )

        self.model: Optional[nn.Module] = None
        self.tokenizer: Optional[AutoTokenizer] = None

    def load_model(self, device: str = "cuda"):
        """Load base model and apply LoRA."""
        print(f"Loading base model: {self.base_model_name}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_name,
            trust_remote_code=True,
        )

        # Ensure padding token exists
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            quantization_config=self.bnb_config if self.use_quantization else None,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True,
            torch_dtype=torch.float16,
        )

        # Apply LoRA
        self.model = get_peft_model(self.model, self.lora_config)
        self.model.print_trainable_parameters()

        print("Model loaded successfully")

    def generate_solution(
        self,
        problem: str,
        max_length: int = 512,
        temperature: float = 0.7,
        num_return_sequences: int = 1,
    ) -> List[str]:
        """
        Generate solution(s) to mathematical problem.

        Args:
            problem: Problem statement
            max_length: Maximum generation length
            temperature: Sampling temperature (lower = more focused)
            num_return_sequences: Number of solutions to generate

        Returns:
            List of generated solutions
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Format prompt
        prompt = f"""Solve the following mathematical problem. Show your work and verify your answer.

Problem: {problem}

Solution:"""

        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )

        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=temperature,
                num_return_sequences=num_return_sequences,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Decode
        solutions = []
        for output in outputs:
            solution = self.tokenizer.decode(output, skip_special_tokens=True)
            # Extract just the solution part (after "Solution:")
            if "Solution:" in solution:
                solution = solution.split("Solution:", 1)[1].strip()
            solutions.append(solution)

        return solutions

    def generate_with_chain_of_thought(
        self,
        problem: str,
        max_steps: int = 10,
    ) -> tuple[str, List[str]]:
        """
        Generate solution with explicit chain-of-thought reasoning.

        Returns:
            Tuple of (final_solution, reasoning_steps)
        """
        prompt = f"""Solve this problem step by step. Number each step.

Problem: {problem}

Step 1:"""

        steps = []
        current_solution = ""

        # Iteratively generate reasoning steps
        for step_num in range(1, max_steps + 1):
            step_prompt = prompt + "\n".join(steps)

            inputs = self.tokenizer(step_prompt, return_tensors="pt", padding=True)
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.3,
                    do_sample=True,
                )

            step = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract new step
            if f"Step {step_num}:" in step:
                new_content = step.split(f"Step {step_num}:", 1)[1]
                if f"Step {step_num + 1}:" in new_content:
                    new_content = new_content.split(f"Step {step_num + 1}:", 1)[0]
                steps.append(f"Step {step_num}: {new_content.strip()}")

            # Check if we have final answer
            if "final answer" in step.lower() or "therefore" in step.lower():
                current_solution = new_content.strip()
                break

        return current_solution, steps

    def save_adapter(self, output_dir: str):
        """Save LoRA adapter weights."""
        if self.model is None:
            raise RuntimeError("No model to save")

        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        print(f"Adapter saved to {output_dir}")

    def load_adapter(self, adapter_path: str):
        """Load fine-tuned LoRA adapter."""
        if self.model is None:
            self.load_model()

        from peft import PeftModel

        self.model = PeftModel.from_pretrained(
            self.model,
            adapter_path,
        )
        print(f"Adapter loaded from {adapter_path}")

    def count_parameters(self) -> Dict[str, int]:
        """Count trainable and total parameters."""
        if self.model is None:
            return {"total": 0, "trainable": 0}

        total = sum(p.numel() for p in self.model.parameters())
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

        return {
            "total": total,
            "trainable": trainable,
            "trainable_percent": 100 * trainable / total if total > 0 else 0,
        }
