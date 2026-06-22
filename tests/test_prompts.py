"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="class")
def prompt_data():
    """Carrega o prompt otimizado uma única vez para a suíte."""
    prompts = load_prompts(PROMPT_FILE)

    assert isinstance(prompts, dict), "O arquivo YAML deve conter um dicionário."
    assert PROMPT_KEY in prompts, f"O YAML deve conter a chave '{PROMPT_KEY}'."

    prompt = prompts[PROMPT_KEY]
    assert isinstance(prompt, dict), f"O prompt '{PROMPT_KEY}' deve ser um dicionário."

    return prompt


def prompt_text(prompt: dict) -> str:
    """Concatena campos textuais relevantes do prompt para validações."""
    return "\n".join(
        str(prompt.get(field, ""))
        for field in ("description", "system_prompt", "user_prompt")
    )


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo 'system_prompt' não encontrado."

        system_prompt = prompt_data["system_prompt"]

        assert isinstance(system_prompt, str), "Campo 'system_prompt' deve ser texto."
        assert system_prompt.strip(), "Campo 'system_prompt' não pode estar vazio."

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_data.get("system_prompt", "")
        normalized_prompt = system_prompt.lower()

        role_definition_pattern = r"\bvoc[êe]\s+[ée]\s+um(?:a)?\b"
        role_keywords = (
            "product owner",
            "product manager",
            "qa",
            "especialista",
            "product",
        )

        assert re.search(role_definition_pattern, normalized_prompt), (
            "O system_prompt deve definir uma persona explicitamente "
            '(ex: "Você é um Product Manager").'
        )
        assert any(keyword in normalized_prompt for keyword in role_keywords), (
            "O system_prompt deve mencionar uma persona ou papel de produto/qualidade."
        )

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        normalized_prompt = prompt_text(prompt_data).lower()

        mentions_markdown = "markdown" in normalized_prompt
        mentions_user_story_template = all(
            phrase in normalized_prompt
            for phrase in ("como", "eu quero", "para que")
        )

        assert mentions_markdown or mentions_user_story_template, (
            "O prompt deve exigir formato Markdown ou o padrão de User Story "
            '("Como...", "Eu quero...", "Para que...").'
        )

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data.get("system_prompt", "")
        normalized_prompt = system_prompt.lower()

        inputs = re.findall(r"^\s*input\s*:", system_prompt, flags=re.IGNORECASE | re.MULTILINE)
        outputs = re.findall(r"^\s*output\s*:", system_prompt, flags=re.IGNORECASE | re.MULTILINE)

        assert "few-shot" in normalized_prompt or "exemplo" in normalized_prompt, (
            "O prompt deve mencionar exemplos ou a técnica Few-shot."
        )
        assert len(inputs) >= 2 and len(outputs) >= 2, (
            "O prompt deve conter pelo menos 2 exemplos com entrada (Input) e saída (Output)."
        )
        assert len(inputs) == len(outputs), (
            "Cada exemplo de entrada (Input) deve ter uma saída (Output) correspondente."
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        serialized_prompt = yaml.safe_dump(
            prompt_data,
            allow_unicode=True,
            sort_keys=False,
        )

        assert not re.search(r"\[?\bTODO\b\]?", serialized_prompt, flags=re.IGNORECASE), (
            "O prompt não deve conter marcadores TODO ou [TODO]."
        )

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied")

        assert isinstance(techniques, list), (
            "O campo 'techniques_applied' deve existir nos metadados e ser uma lista."
        )
        assert len(techniques) >= 2, (
            "O prompt deve listar pelo menos 2 técnicas em 'techniques_applied'."
        )
        assert all(isinstance(technique, str) and technique.strip() for technique in techniques), (
            "Todas as técnicas listadas devem ser textos não vazios."
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
