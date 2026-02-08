# MLflow Implementation Guide - Step-by-Step

## Current Status: Infrastructure Complete ✅

**Completed** (Steps 1-4):
- ✅ MLflow added to requirements.txt
- ✅ MLflow configuration file created (`config/mlflow_config.yaml`)
- ✅ MLflow wrapper module created (`src/training/mlflow_logger.py`)
- ✅ MLflow launch script created (`scripts/launch_mlflow.sh`)

**Remaining** (Steps 5-8):
- ⏳ Instrument training scripts with MLflow logging
- ⏳ Run training to generate experiment history
- ⏳ Add MLflow documentation to README
- ⏳ Screenshot MLflow UI for portfolio

---

## Step 5: Instrument Training Scripts (4-6 hours)

### 5.1: Install MLflow First

```bash
cd project-1-technical-rag
pip install mlflow>=2.9.0
```

### 5.2: Add MLflow to train_epic1_complete.py

**Location**: `scripts/epic1_training/train_epic1_complete.py` (use pathlib to resolve from script location)

**Add imports at top** (after line 50):
```python
# Add after existing imports
from src.training.mlflow_logger import get_mlflow_logger

# Initialize MLflow logger
mlflow_logger = get_mlflow_logger()
```

**Find the `Epic1CompleteTrainer` class** (around line 200-300) and instrument the `train_view_model` method:

```python
def train_view_model(self, view_name: str, samples: List[Dict], epochs: int = 100) -> Dict:
    """Train a single view model with MLflow tracking."""

    logger.info(f"Training {view_name} view model...")

    # START MLFLOW RUN
    with mlflow_logger.start_run(
        experiment_name="epic1-view-models",
        run_name=f"{view_name}_view_training",
        tags={
            "view": view_name,
            "epic": "1",
            "component": "query_analyzer"
        }
    ):
        # Log hyperparameters
        mlflow_logger.log_params({
            "view_name": view_name,
            "epochs": epochs,
            "learning_rate": 0.001,
            "batch_size": 64,
            "hidden_dim": 128,
            "dropout": 0.3,
            "optimizer": "AdamW",
            "weight_decay": 0.01,
            "train_samples": len(train_dataset),
            "val_samples": len(val_dataset),
            "feature_dim": 10,
            "seed": SEED
        })

        # EXISTING TRAINING LOOP (keep as-is)
        for epoch in range(epochs):
            # ... existing training code ...

            # LOG METRICS PER EPOCH (add this inside the epoch loop)
            mlflow_logger.log_metrics({
                "train_loss": avg_train_loss,
                "val_loss": avg_val_loss,
                "val_mae": val_mae,
                "learning_rate": optimizer.param_groups[0]['lr']
            }, step=epoch)

        # After training completes, log final metrics
        mlflow_logger.log_metrics({
            "final_val_loss": best_val_loss,
            "final_val_mae": best_val_mae,
            "final_train_loss": final_train_loss
        })

        # Log the trained model
        mlflow_logger.log_model(
            model,
            artifact_path=f"models/{view_name}_view",
            registered_model_name=f"epic1_{view_name}_view_model"
        )

        # Log training results as JSON
        results = {
            "view": view_name,
            "final_val_loss": float(best_val_loss),
            "final_val_mae": float(best_val_mae),
            "epochs_trained": epochs,
            "best_epoch": best_epoch
        }
        mlflow_logger.log_dict(results, f"{view_name}_results.json")

    return results  # existing return
```

### 5.3: Instrument Fusion Training

**Find the `train_fusion_layer` method** and add similar MLflow logging:

```python
def train_fusion_layer(self, fusion_type: str = "weighted") -> Dict:
    """Train fusion layer with MLflow tracking."""

    with mlflow_logger.start_run(
        experiment_name="epic1-fusion-layer",
        run_name=f"fusion_{fusion_type}",
        tags={
            "fusion_type": fusion_type,
            "epic": "1",
            "component": "fusion_layer"
        }
    ):
        # Log fusion hyperparameters
        mlflow_logger.log_params({
            "fusion_type": fusion_type,
            "num_views": 5,
            "view_names": ["technical", "linguistic", "task", "semantic", "computational"]
        })

        # ... existing training code ...

        # Log fusion results
        mlflow_logger.log_metrics({
            "fusion_mae": mae,
            "fusion_mse": mse,
            "fusion_r2": r2_score
        })

        # Log fusion weights if weighted fusion
        if fusion_type == "weighted" and hasattr(self, 'fusion_weights'):
            mlflow_logger.log_params({
                f"weight_{view}": float(weight)
                for view, weight in self.fusion_weights.items()
            })

        # Log fusion model
        mlflow_logger.log_model(
            fusion_model,
            artifact_path="models/fusion_layer",
            registered_model_name=f"epic1_fusion_{fusion_type}"
        )

    return results
```

### 5.4: Modify main() function

**Find the `main()` function** (bottom of file) and wrap the entire pipeline:

```python
def main():
    """Main training pipeline with MLflow tracking."""

    # Parse arguments (existing code)
    args = parse_args()

    # Top-level MLflow run for the complete pipeline
    with mlflow_logger.start_run(
        experiment_name="epic1-complete-pipeline",
        run_name=f"complete_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        tags={
            "epic": "1",
            "pipeline": "complete",
            "mode": "quick" if args.quick else "full"
        }
    ):
        # Log pipeline configuration
        mlflow_logger.log_params({
            "views_only": args.views_only,
            "fusion_only": args.fusion_only,
            "quick_mode": args.quick,
            "dataset_size": len(samples),
            "seed": SEED
        })

        # Initialize trainer (existing)
        trainer = Epic1CompleteTrainer()

        # Phase 1: Train view models (existing code - now with nested MLflow runs)
        if not args.fusion_only:
            trainer.train_all_view_models(samples, epochs=...)

        # Phase 2: Train fusion (existing code - now with nested MLflow runs)
        if not args.views_only:
            trainer.train_fusion_layer(...)

        # Log overall pipeline metrics
        mlflow_logger.log_metrics({
            "total_training_time_seconds": total_time,
            "pipeline_success": 1.0
        })

        logger.info("✅ Complete MLflow-tracked training pipeline finished!")
        logger.info(f"View results at: http://localhost:5000")
```

---

## Step 6: Run Training to Generate Experiments (2 hours)

### 6.1: Launch MLflow UI (Terminal 1)

```bash
cd project-1-technical-rag
./scripts/launch_mlflow.sh
```

**Expected Output**:
```
========================================
  MLflow UI Launcher
========================================

Starting MLflow UI...
  Backend Store: file:./mlruns
  Artifact Root: ./mlartifacts
  Port: 5000

Access MLflow UI at: http://localhost:5000
Press Ctrl+C to stop
```

**Navigate to**: http://localhost:5000 (should see empty MLflow interface)

### 6.2: Run Quick Training (Terminal 2)

```bash
cd project-1-technical-rag
python scripts/epic1_training/train_epic1_complete.py --quick
```

**Expected**:
- Training runs with MLflow logging
- MLflow UI shows experiments in real-time
- Models saved to MLflow registry

### 6.3: Run Multiple Experiments

**Experiment 1: Baseline (quick mode)**
```bash
python scripts/epic1_training/train_epic1_complete.py --quick
```

**Experiment 2: Full training**
```bash
python scripts/epic1_training/train_epic1_complete.py
```

**Experiment 3: Views only**
```bash
python scripts/epic1_training/train_epic1_complete.py --views-only
```

**Experiment 4: Fusion only** (after training views)
```bash
python scripts/epic1_training/train_epic1_complete.py --fusion-only
```

### 6.4: Verify in MLflow UI

Check http://localhost:5000:
- ✅ See "epic1-view-models" experiment with 5 runs (one per view)
- ✅ See "epic1-fusion-layer" experiment with fusion runs
- ✅ See "epic1-complete-pipeline" parent runs
- ✅ Click any run → see hyperparameters, metrics, models

---

## Step 7: Add MLflow Documentation to README (1 hour)

### 7.1: Add MLflow Section to project-1-technical-rag/README.md

**Add after "Testing" section, before "Deployment Options"**:

```markdown
## 🧪 ML Experiment Tracking with MLflow

### Quick Start

```bash
# 1. Install dependencies (includes MLflow)
pip install -r requirements.txt

# 2. Launch MLflow UI (Terminal 1)
./scripts/launch_mlflow.sh

# 3. Run training (Terminal 2)
python scripts/epic1_training/train_epic1_complete.py --quick

# 4. View experiments
# Navigate to: http://localhost:5000
```

### MLflow Features

**Experiment Tracking**:
- All training runs logged with hyperparameters and metrics
- Compare multiple model configurations side-by-side
- Track training/validation metrics across epochs
- Full reproducibility with logged configurations

**Model Registry**:
- Trained models registered with versioning
- Models: `epic1_{view}_view_model`, `epic1_fusion_{type}`
- Load any model version for inference
- Production/staging model promotion

**Experiments Organization**:
- `epic1-view-models`: Individual view model training (5 views)
- `epic1-fusion-layer`: Ensemble fusion strategies
- `epic1-complete-pipeline`: End-to-end training pipelines

### Example: View Experiment Results

```python
import mlflow

# Set tracking URI
mlflow.set_tracking_uri("file:./mlruns")

# Get experiment
experiment = mlflow.get_experiment_by_name("epic1-view-models")

# List all runs
runs = mlflow.search_runs(experiment.experiment_id)
print(runs[['metrics.final_val_mae', 'params.view_name', 'params.epochs']])

# Load best model
best_run = runs.sort_values('metrics.final_val_mae').iloc[0]
model = mlflow.pytorch.load_model(f"runs:/{best_run.run_id}/models/technical_view")
```

### MLflow Configuration

Configuration: `config/mlflow_config.yaml`

**Development** (default):
- Local file-based tracking: `file:./mlruns`
- Local artifacts: `./mlartifacts`

**Production** (optional):
- Remote tracking server via `MLFLOW_TRACKING_URI`
- Shared artifact storage (S3, GCS, Azure)

See `MLFLOW_IMPLEMENTATION_GUIDE.md` for detailed setup instructions.
```

---

## Step 8: Screenshot MLflow UI for Portfolio (30 minutes)

### 8.1: Take Screenshots

With MLflow UI running and experiments visible:

**Screenshot 1: Experiment List**
- Navigate to: http://localhost:5000
- Show all experiments (epic1-view-models, epic1-fusion-layer, epic1-complete-pipeline)
- Save as: `docs/assets/mlflow-experiments.png`

**Screenshot 2: Run Comparison**
- Select "epic1-view-models" experiment
- Select all 5 view model runs (technical, linguistic, task, semantic, computational)
- Click "Compare" button
- Show parallel coordinates plot of hyperparameters and metrics
- Save as: `docs/assets/mlflow-comparison.png`

**Screenshot 3: Model Registry**
- Click "Models" tab
- Show registered models with versions
- Save as: `docs/assets/mlflow-models.png`

### 8.2: Add Screenshots to README

**Update project-1-technical-rag/README.md** (in MLflow section):

```markdown
### MLflow Dashboard

![MLflow Experiments](docs/assets/mlflow-experiments.png)
*Epic 1 experiments tracked in MLflow: view models, fusion layers, and complete pipelines*

![MLflow Run Comparison](docs/assets/mlflow-comparison.png)
*Comparing 5 view models across hyperparameters and validation metrics*
```

### 8.3: Add to Root README

**Update README.md in project root** (in Project 1 section):

```markdown
### Project 1: Technical Documentation RAG System
📂 **`project-1-technical-rag/`** - RAG system for technical documentation
- **Status**: Production-grade architecture with MLflow experiment tracking
- **Architecture**: 6-component modular system with 97 sub-components
- **Features**: Multi-model routing, hybrid retrieval (FAISS + BM25), neural reranking
- **Testing**: 2,555 test functions with comprehensive coverage
- **MLOps**: MLflow tracking with model registry and reproducibility
- **Deployment**: K8s/Helm infrastructure with multi-cloud support (AWS EKS/ECS, GCP, Azure)
```

---

## Validation Checklist

After completing all steps, verify:

- [ ] `pip list | grep mlflow` shows mlflow>=2.9.0
- [ ] `./scripts/launch_mlflow.sh` launches UI successfully
- [ ] http://localhost:5000 displays MLflow interface
- [ ] Training script runs without errors
- [ ] MLflow UI shows experiments in real-time during training
- [ ] Can see hyperparameters logged for each run
- [ ] Can see metrics (train_loss, val_loss, etc.) across epochs
- [ ] Models appear in MLflow registry
- [ ] Can load model from registry with `mlflow.pytorch.load_model()`
- [ ] README has MLflow section with documentation
- [ ] Screenshots show MLflow dashboard with experiments

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'mlflow'"
**Solution**: `pip install mlflow>=2.9.0`

### Issue: "ImportError: cannot import name 'get_mlflow_logger'"
**Solution**: Ensure `src/training/mlflow_logger.py` exists and is in PYTHONPATH
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: MLflow UI shows no experiments
**Solution**:
1. Check mlruns/ directory exists
2. Verify training script completed successfully
3. Check tracking URI matches: `file:./mlruns`

### Issue: Training fails with MLflow errors
**Solution**: Disable MLflow temporarily to debug:
```python
# In mlflow_config.yaml, set all logging to false
logging:
  log_params: false
  log_metrics: false
  log_models: false
  log_artifacts: false
```

---

## Time Estimate

**Remaining Work**:
- Step 5 (Instrumentation): 4-6 hours
- Step 6 (Run Experiments): 2 hours
- Step 7 (Documentation): 1 hour
- Step 8 (Screenshots): 30 minutes

**Total**: 7.5-9.5 hours

**Aggressive Timeline**: Can be done in one weekend
- Saturday: Steps 5-6 (6-8 hours)
- Sunday: Steps 7-8 (1.5 hours)

---

## Impact on Portfolio

**Before MLflow** (3.9/5):
- ❌ No experiment tracking
- ❌ Cannot demonstrate ML engineering maturity
- ❌ Auto-reject from mid-size+ Swiss companies

**After MLflow Priority 1** (4.1/5):
- ✅ Professional experiment tracking
- ✅ Model registry with versioning
- ✅ Reproducible training runs
- ✅ Screenshots showing MLOps expertise
- ✅ **Can apply to mid-size Swiss companies**

**For Interviews**:
> "I use MLflow for experiment tracking. Here's my dashboard showing 12 training runs across 5 view models. I can show you how hyperparameters affect validation MAE, compare fusion strategies, and explain my model selection criteria. All experiments are fully reproducible."

---

**Next Steps**: Begin with Step 5.2 (instrumenting train_epic1_complete.py) when ready to continue implementation.
