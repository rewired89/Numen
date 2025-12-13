"""
Complete guide to training LoRA on Lean code generation.

This teaches the model to output formal Lean 4 proofs instead of natural language.
"""

from typing import List, Dict
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset


class LeanCodeTrainer:
    """
    Train model to generate Lean 4 code using LoRA fine-tuning.

    Process:
    1. Create dataset of (problem, lean_proof) pairs
    2. Fine-tune model with LoRA
    3. Model learns to output Lean syntax
    """

    def __init__(
        self,
        base_model: str = "deepseek-ai/deepseek-math-7b-base",
        output_dir: str = "checkpoints/lean-lora",
    ):
        self.base_model_name = base_model
        self.output_dir = output_dir

    def create_training_dataset(self) -> Dataset:
        """
        Create dataset of (natural_language_problem, lean_proof) pairs.

        Example format:
        {
            "problem": "Prove there are infinitely many primes",
            "lean_code": "theorem infinitely_many_primes : ∀ n, ∃ p ≥ n, Nat.Prime p := by..."
        }
        """

        # Example training data
        training_examples = [
            {
                "problem": "Prove there are infinitely many primes",
                "lean_code": """
theorem infinitely_many_primes : ∀ n, ∃ p ≥ n, Nat.Prime p := by
  intro n
  let N := (Nat.factorial n) + 1
  have ⟨p, hp_prime, hp_dvd⟩ := exists_prime_factor (Nat.factorial_pos n)
  exists p
  constructor
  · by_contra h
    push_neg at h
    have : p ∣ Nat.factorial n := Nat.Prime.dvd_factorial hp_prime h
    have : p ∣ 1 := (Nat.dvd_add_right this).mp hp_dvd
    exact Nat.Prime.not_dvd_one hp_prime this
  · exact hp_prime
""",
            },
            {
                "problem": "Prove that √2 is irrational",
                "lean_code": """
theorem sqrt_two_irrational : Irrational (Real.sqrt 2) := by
  intro ⟨q, hq⟩
  have h : (q : ℝ)^2 = 2 := by
    rw [← hq]
    exact sq_sqrt (by norm_num : (0 : ℝ) ≤ 2)
  have : (q.num^2 : ℤ) = 2 * q.den^2 := by
    have := congr_arg (· * q.den^2) h
    simp at this
    exact this
  -- Continue proof...
  sorry
""",
            },
            {
                "problem": "Sum of first n natural numbers equals n(n+1)/2",
                "lean_code": """
theorem sum_first_n (n : ℕ) : 2 * (Finset.range (n + 1)).sum id = n * (n + 1) := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Finset.sum_range_succ, mul_add, ih]
    ring
""",
            },
        ]

        # Format for training
        formatted_data = []
        for example in training_examples:
            # Create prompt-completion pair
            prompt = f"""Convert this mathematical problem to Lean 4 code:

Problem: {example['problem']}

Lean 4 code:
"""
            completion = example['lean_code']

            formatted_data.append({
                "prompt": prompt,
                "completion": completion,
            })

        return Dataset.from_list(formatted_data)

    def setup_lora(self, model):
        """
        Setup LoRA for efficient fine-tuning.

        LoRA adds small trainable matrices to the model instead of
        retraining all billions of parameters.

        Parameters we tune:
        - r: LoRA rank (typically 8-64)
        - alpha: Scaling factor
        - target_modules: Which layers to adapt
        """

        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,  # LoRA rank - controls how many parameters we add
            lora_alpha=32,  # Scaling factor
            lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # Attention layers
            bias="none",
        )

        # Apply LoRA to model
        model = get_peft_model(model, lora_config)

        print("LoRA Configuration:")
        model.print_trainable_parameters()
        # Output example: "trainable params: 4,194,304 || all params: 7,000,000,000 || trainable%: 0.06%"

        return model

    def train(
        self,
        epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-4,
    ):
        """
        Train the model to generate Lean code.

        Process:
        1. Load base model (DeepSeek-Math or Llama)
        2. Add LoRA adapters
        3. Train on (problem, lean_code) pairs
        4. Model learns to output Lean syntax
        """

        print("Step 1: Loading base model...")
        tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            torch_dtype=torch.float16,
            device_map="auto",
        )

        print("Step 2: Adding LoRA adapters...")
        model = self.setup_lora(model)

        print("Step 3: Creating dataset...")
        dataset = self.create_training_dataset()

        # Tokenize dataset
        def tokenize_function(examples):
            # Combine prompt and completion
            texts = [p + c for p, c in zip(examples["prompt"], examples["completion"])]
            return tokenizer(texts, truncation=True, max_length=512)

        tokenized_dataset = dataset.map(tokenize_function, batched=True)

        print("Step 4: Training...")
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            learning_rate=learning_rate,
            save_steps=100,
            logging_steps=10,
            fp16=True,
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
        )

        trainer.train()

        print("Step 5: Saving LoRA weights...")
        model.save_pretrained(self.output_dir)
        tokenizer.save_pretrained(self.output_dir)

        print(f"✅ LoRA training complete! Model saved to {self.output_dir}")


def example_usage():
    """
    Example: How to use the trained model.
    """

    # Train LoRA
    trainer = LeanCodeTrainer()
    trainer.train(epochs=3)

    # Load trained model
    from peft import PeftModel

    base_model = AutoModelForCausalLM.from_pretrained("deepseek-ai/deepseek-math-7b-base")
    model = PeftModel.from_pretrained(base_model, "checkpoints/lean-lora")
    tokenizer = AutoTokenizer.from_pretrained("checkpoints/lean-lora")

    # Generate Lean code
    prompt = "Convert to Lean 4: Prove that 2 + 2 = 4"
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=200)
    lean_code = tokenizer.decode(outputs[0])

    print(lean_code)
    # Output: "theorem two_plus_two : 2 + 2 = 4 := by norm_num"


if __name__ == "__main__":
    """
    To actually run training:

    1. Install dependencies:
       pip install transformers peft datasets accelerate

    2. Prepare dataset (need 1000+ examples):
       - Scrape Lean 4 GitHub repositories
       - Use mathlib (Lean's math library)
       - Generate synthetic examples

    3. Run training:
       python lean_code_trainer.py

    4. Time: ~6-12 hours on single A100 GPU

    5. Result: Model that outputs Lean code instead of English
    """

    trainer = LeanCodeTrainer()
    trainer.train(epochs=3, batch_size=4)
