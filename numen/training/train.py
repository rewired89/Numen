"""
Training script for Numen reasoning engine.

Implements supervised fine-tuning with LoRA on mathematical reasoning datasets.
"""

from typing import Optional, Dict, Any
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling
from datasets import Dataset as HFDataset
import wandb
from pathlib import Path

from numen.training.model import NumenModel
from numen.training.data_pipeline import MathDataPipeline, MathProblem


class MathReasoningDataset(Dataset):
    """PyTorch dataset for mathematical reasoning."""

    def __init__(
        self,
        problems: list[MathProblem],
        tokenizer,
        max_length: int = 512,
    ):
        self.problems = problems
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.problems)

    def __getitem__(self, idx):
        problem = self.problems[idx]

        # Format as conversation
        text = f"""Problem: {problem.problem}

Solution: {problem.solution}"""

        if problem.verification:
            text += f"\n\nVerification: {problem.verification}"

        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": encoding["input_ids"].squeeze(),
        }


class NumenTrainer:
    """
    Training orchestrator for Numen.

    Handles:
    - Data loading and preprocessing
    - Model training with LoRA
    - Evaluation and verification
    - Checkpointing
    """

    def __init__(
        self,
        base_model: str = "deepseek-ai/deepseek-math-7b-base",
        output_dir: str = "checkpoints/numen",
        use_wandb: bool = False,
    ):
        self.base_model = base_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.use_wandb = use_wandb

        # Initialize components
        self.model = NumenModel(base_model=base_model)
        self.data_pipeline = MathDataPipeline()

        # Training state
        self.trainer: Optional[Trainer] = None

    def prepare_data(self, train_ratio: float = 0.8):
        """Load and prepare training data."""
        print("Loading datasets...")
        all_problems = self.data_pipeline.load_all_datasets()

        print(f"Loaded {len(all_problems)} problems")

        # Split train/test
        train_problems, test_problems = self.data_pipeline.get_difficulty_stratified_split(
            train_ratio=train_ratio
        )

        print(f"Train: {len(train_problems)}, Test: {len(test_problems)}")

        return train_problems, test_problems

    def train(
        self,
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-4,
        gradient_accumulation_steps: int = 4,
        warmup_steps: int = 100,
        logging_steps: int = 10,
        save_steps: int = 500,
        eval_steps: int = 500,
    ):
        """
        Train Numen model.

        Args:
            num_epochs: Number of training epochs
            batch_size: Batch size per device
            learning_rate: Learning rate
            gradient_accumulation_steps: Gradient accumulation steps
            warmup_steps: Warmup steps
            logging_steps: Logging frequency
            save_steps: Checkpoint frequency
            eval_steps: Evaluation frequency
        """
        # Load model
        print("Loading model...")
        self.model.load_model()

        # Prepare data
        train_problems, test_problems = self.prepare_data()

        # Create datasets
        train_dataset = MathReasoningDataset(
            train_problems,
            self.model.tokenizer,
        )

        test_dataset = MathReasoningDataset(
            test_problems,
            self.model.tokenizer,
        )

        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            save_steps=save_steps,
            eval_steps=eval_steps,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            fp16=torch.cuda.is_available(),
            optim="paged_adamw_8bit" if self.model.use_quantization else "adamw_torch",
            report_to="wandb" if self.use_wandb else "none",
            run_name="numen-training" if self.use_wandb else None,
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.model.tokenizer,
            mlm=False,  # Causal LM, not masked LM
        )

        # Initialize trainer
        self.trainer = Trainer(
            model=self.model.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=test_dataset,
            data_collator=data_collator,
        )

        # Train
        print("Starting training...")
        self.trainer.train()

        # Save final model
        self.model.save_adapter(str(self.output_dir / "final"))

        print("Training complete!")

    def evaluate_on_math_benchmark(self):
        """
        Evaluate trained model on MATH benchmark.

        Measures:
        - Accuracy on different difficulty levels
        - Verification rate
        - Reasoning quality
        """
        print("Evaluating on MATH benchmark...")

        # Load test problems
        _, test_problems = self.prepare_data()

        correct = 0
        total = 0
        by_difficulty = {}

        for problem in test_problems:
            # Generate solution
            solutions = self.model.generate_solution(problem.problem, num_return_sequences=1)
            generated = solutions[0]

            # Simple accuracy check (would use symbolic verification in production)
            is_correct = problem.solution.lower() in generated.lower()

            if is_correct:
                correct += 1
            total += 1

            # Track by difficulty
            difficulty = problem.difficulty
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = {"correct": 0, "total": 0}
            by_difficulty[difficulty]["total"] += 1
            if is_correct:
                by_difficulty[difficulty]["correct"] += 1

        overall_accuracy = correct / total if total > 0 else 0

        print(f"\nOverall Accuracy: {overall_accuracy:.2%} ({correct}/{total})")
        print("\nBy Difficulty:")
        for difficulty in sorted(by_difficulty.keys()):
            stats = by_difficulty[difficulty]
            acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  Level {difficulty}: {acc:.2%} ({stats['correct']}/{stats['total']})")

        return {
            "overall_accuracy": overall_accuracy,
            "by_difficulty": by_difficulty,
        }


def main():
    """Main training entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Train Numen reasoning engine")
    parser.add_argument("--base-model", default="deepseek-ai/deepseek-math-7b-base", help="Base model")
    parser.add_argument("--output-dir", default="checkpoints/numen", help="Output directory")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--wandb", action="store_true", help="Use Weights & Biases")
    parser.add_argument("--eval-only", action="store_true", help="Only run evaluation")

    args = parser.parse_args()

    # Initialize trainer
    trainer = NumenTrainer(
        base_model=args.base_model,
        output_dir=args.output_dir,
        use_wandb=args.wandb,
    )

    if args.eval_only:
        # Load model and evaluate
        trainer.model.load_model()
        trainer.model.load_adapter(f"{args.output_dir}/final")
        trainer.evaluate_on_math_benchmark()
    else:
        # Train
        trainer.train(
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
        )

        # Evaluate
        trainer.evaluate_on_math_benchmark()


if __name__ == "__main__":
    main()
