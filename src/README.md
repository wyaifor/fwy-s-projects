# COMP5329 A2

This is a research-oriented CLIP occupation-bias project using FairFace demographic images, a FACET-derived broad occupation prompt set, optional BLS/ABS labour-statistics comparison, and a downstream recommendation scenario simulation.

## Research Question

Do CLIP image-text embeddings associate demographic groups with occupations in ways that differ across race and gender, diverge from aggregate labour statistics, and propagate into simplified retrieval or recommendation outputs?

Working hypotheses:

1. CLIP exhibits measurable demographic variation in occupation-prompt association scores.
2. Some CLIP occupation associations may diverge from or amplify real-world occupation distributions.
3. Embedding-level associations may propagate into downstream retrieval or recommendation behavior.

FairFace has demographic labels but no true occupation labels. Results measure CLIP association patterns, not real occupation prediction and not FACET image evaluation.

## Notebook Workflow

Run the notebooks in this order:

1. Main FairFace CLIP association notebook:

```text
src/notebooks/04_fairface_facet_broad_occupation_bias.ipynb
```

This notebook loads FairFace, builds FACET-derived occupation prompts, encodes images/text with CLIP, and saves association tables, figures, and embeddings.

2. Stage 4 real-world distribution comparison:

```text
src/notebooks/stage4_realworld_distribution_comparison.ipynb
```

This notebook loads outputs from the main notebook and compares mapped CLIP gender association gaps with BLS aggregate occupation gender statistics. ABS comparison is treated conservatively and only generated if the available data and mapping support it.

3. Stage 5 recommendation scenario simulation:

```text
src/notebooks/stage5_recommendation_scenario_simulation.ipynb
```

This notebook loads saved embeddings and metadata from the main notebook, constructs synthetic users, recommends occupation prompts by cosine similarity, and evaluates top-k disparity, sensitivity, and bootstrap uncertainty.

Earlier/supporting notebooks:

```text
src/notebooks/01_fairface_clip_occupation_bias.ipynb
src/notebooks/03_facet_data_and_occupation_design.ipynb
```

## Project Structure

```text
.
|-- configs/
|   |-- occupations_facet_broad.yml
|   `-- occupation_realworld_mapping.csv
|-- src/
|   |-- clip_bias/
|   |   |-- analysis.py
|   |   |-- config.py
|   |   |-- data.py
|   |   |-- model.py
|   |   |-- realworld.py
|   |   `-- recommendation.py
|   `-- notebooks/
|-- tests/
|-- environment.yml
|-- pyproject.toml
`-- README.md
```

## Environment Setup

Conda:

```bash
conda env create -f environment.yml
conda activate clip-bias-fairface
pip install -e .
```

Pip/Colab:

```bash
pip install -e .
pip install transformers accelerate statsmodels seaborn pytest openpyxl
```

The project uses HuggingFace `transformers` CLIP (`openai/clip-vit-base-patch32`). No separate OpenAI CLIP package is required.

## Supported Data Layouts

FairFace can be placed in either layout:

```text
data/fairface/fairface_label_train.csv
data/fairface/fairface_label_val.csv
data/fairface/train/
data/fairface/val/
```

or:

```text
fairface/fairface_label_train.csv
fairface/fairface_label_val.csv
fairface/train/
fairface/val/
```

Optional BLS/ABS/FACET data can also use either root-level or `data/` layouts:

```text
data/bls/raw/     or bls/raw/
data/abs/raw/     or abs/raw/
data/facet/       or facet/
```

## Running on Google Colab

Upload and unzip the whole project, not a single notebook:

```python
from google.colab import files
uploaded = files.upload()
```

```bash
!unzip COMP5329_A2-main-research-ready.zip -d /content/
%cd /content/COMP5329_A2-main
```

Upload and unzip the data archive into the project root:

```python
from google.colab import files
uploaded = files.upload()
```

```bash
!unzip data.zip -d /content/COMP5329_A2-main/
```

Install dependencies from the project root:

```bash
!pip install -e .
!pip install transformers accelerate statsmodels seaborn pytest openpyxl
```

Then run the notebooks in order:

```text
1. src/notebooks/04_fairface_facet_broad_occupation_bias.ipynb
2. src/notebooks/stage4_realworld_distribution_comparison.ipynb
3. src/notebooks/stage5_recommendation_scenario_simulation.ipynb
```

Use a GPU runtime for the main notebook because CLIP image encoding is slow on CPU. Stage 4 and Stage 5 load saved tables/embeddings and should not recompute CLIP embeddings.

## Outputs

Main notebook:

```text
outputs/fairface_facet_broad/tables/sampled_fairface_labels.csv
outputs/fairface_facet_broad/tables/occupation_prompts.csv
outputs/fairface_facet_broad/tables/occupation_similarity_scores.csv
outputs/fairface_facet_broad/tables/gender_gap_by_occupation.csv
outputs/fairface_facet_broad/tables/race_gap_by_occupation.csv
outputs/fairface_facet_broad/embeddings/image_embeddings.npy
outputs/fairface_facet_broad/embeddings/text_embeddings.npy
outputs/fairface_facet_broad/figures/
```

Stage 4:

```text
outputs/realworld/tables/occupation_realworld_mapping_used.csv
outputs/realworld/tables/clip_vs_bls_gender_gap.csv
outputs/realworld/tables/clip_vs_abs_comparison.csv    # only if feasible
outputs/realworld/tables/abs_comparison_todo.md        # if ABS is not feasible
outputs/realworld/figures/clip_vs_bls_gender_gap_scatter.png
outputs/realworld/figures/realworld_amplification_top_occupations.png
```

Stage 5:

```text
outputs/recommendation/tables/synthetic_user_recommendations.csv
outputs/recommendation/tables/topk_occupation_distribution_by_group.csv
outputs/recommendation/tables/recommendation_disparity_by_occupation.csv
outputs/recommendation/tables/recommendation_sensitivity_results.csv
outputs/recommendation/tables/recommendation_sensitivity_summary.csv
outputs/recommendation/tables/recommendation_disparity_bootstrap_ci.csv
outputs/recommendation/figures/topk_distribution_heatmap.png
outputs/recommendation/figures/recommendation_disparity_top_occupations.png
outputs/recommendation/figures/recommendation_sensitivity_top_disparities.png
```

## Troubleshooting

`ModuleNotFoundError: clip_bias`

```bash
pip install -e .
```

FairFace path not found:

Check that FairFace is under either `data/fairface/` or `fairface/`.

Missing `image_embeddings.npy` or `text_embeddings.npy`:

Run the main notebook first. Stage 5 expects embeddings under:

```text
outputs/fairface_facet_broad/embeddings/
```

BLS/ABS comparison missing:

Stage 4 only reports real-world comparison when data and occupation mappings are usable. Otherwise it writes a TODO/diagnostic note under `outputs/realworld/tables/`.

## GitHub Safety

Safe to commit:

```text
.gitignore
README.md
environment.yml
pyproject.toml
PROJECT_PLAN.md
configs/
scripts/
src/
tests/
```

Do not commit:

```text
data/
fairface/
facet/
bls/
abs/
outputs/
*.npy
*.pt
*.pth
*.ckpt
__pycache__/
.ipynb_checkpoints/
.pytest_cache/
```

Raw datasets, FairFace images, model caches, saved embeddings, and generated outputs should remain local or in Colab/Drive only.
