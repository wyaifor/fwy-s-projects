from pathlib import Path

import yaml


def load_occupation_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if "prompt_templates" not in config or "occupations" not in config:
        raise ValueError("Config must contain 'prompt_templates' and 'occupations'.")
    return config


def flatten_occupations(config: dict) -> list[dict]:
    rows = []
    for category, occupations in config["occupations"].items():
        for occupation in occupations:
            rows.append({"occupation": occupation, "category": category})
    return rows


def build_prompts(config: dict) -> list[dict]:
    rows = []
    for occ in flatten_occupations(config):
        for template in config["prompt_templates"]:
            rows.append(
                {
                    "occupation": occ["occupation"],
                    "category": occ["category"],
                    "template": template,
                    "prompt": template.format(occupation=occ["occupation"]),
                }
            )
    return rows
