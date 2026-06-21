"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import check_env_vars, load_yaml, print_section_header

load_dotenv()

PROMPT_FILE = Path("prompts/bug_to_user_story_v2.yml")
PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_SLUG = "bug_to_user_story_v2"
REQUIRED_FIELDS = ("description", "system_prompt", "user_prompt", "version")


def _ensure_langsmith_compat_env() -> None:
    """Mantem compatibilidade com clientes que ainda usam variaveis LANGCHAIN_*."""
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    if langsmith_api_key and not os.getenv("LANGCHAIN_API_KEY"):
        os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key

    langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")
    if langsmith_endpoint and not os.getenv("LANGCHAIN_ENDPOINT"):
        os.environ["LANGCHAIN_ENDPOINT"] = langsmith_endpoint


def _as_text_list(value: Any) -> list[str]:
    """Normaliza campos de metadados que devem ser listas de strings."""
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _build_prompt_template(prompt_data: dict) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", prompt_data["system_prompt"]),
            ("human", prompt_data["user_prompt"]),
        ]
    )


def _push_with_compatible_args(
    prompt_name: str,
    prompt_template: ChatPromptTemplate,
    prompt_data: dict,
) -> str:
    """
    Publica usando argumentos modernos e faz fallback para instalacoes antigas
    do LangChain que aceitam apenas o conjunto basico.
    """
    description = prompt_data.get("description", "")
    tags = _as_text_list(prompt_data.get("tags"))
    techniques = _as_text_list(prompt_data.get("techniques_applied"))

    metadata = {
        "version": prompt_data.get("version"),
        "tags": tags,
        "techniques_applied": techniques,
    }
    metadata = {key: value for key, value in metadata.items() if value}

    try:
        return hub.push(
            prompt_name,
            prompt_template,
            new_repo_is_public=True,
            new_repo_description=description,
            tags=tags,
            metadata=metadata,
        )
    except TypeError:
        try:
            return hub.push(
                prompt_name,
                prompt_template,
                new_repo_is_public=True,
                new_repo_description=description,
            )
        except TypeError:
            return hub.push(prompt_name, prompt_template)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        prompt_template = _build_prompt_template(prompt_data)
        url = _push_with_compatible_args(prompt_name, prompt_template, prompt_data)

        print(f"Prompt publicado com sucesso: {prompt_name}")
        if url:
            print(f"URL: {url}")
        print("Visibilidade solicitada: publico")
        return True
    except Exception as error:
        print(f"Erro ao fazer push do prompt '{prompt_name}': {error}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list[str]]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    if not isinstance(prompt_data, dict):
        return False, ["Estrutura do prompt deve ser um dicionario."]

    for field in REQUIRED_FIELDS:
        value = prompt_data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"Campo obrigatorio ausente ou vazio: {field}")

    version = str(prompt_data.get("version", "")).strip().lower()
    if version != "v2":
        errors.append("Campo version deve ser 'v2'.")

    system_prompt = str(prompt_data.get("system_prompt", ""))
    user_prompt = str(prompt_data.get("user_prompt", ""))
    full_prompt = f"{system_prompt}\n{user_prompt}"

    todo_markers = ("[TODO]", "TODO:", "TODO ")
    if any(marker in full_prompt.upper() for marker in todo_markers):
        errors.append("Prompt ainda contem TODO.")

    if "{bug_report}" not in user_prompt:
        errors.append("user_prompt deve declarar o placeholder {bug_report}.")

    if len(_as_text_list(prompt_data.get("techniques_applied"))) < 2:
        errors.append("Informe pelo menos 2 tecnicas em techniques_applied.")

    if not _as_text_list(prompt_data.get("tags")):
        errors.append("Informe pelo menos uma tag em tags.")

    return len(errors) == 0, errors


def main() -> int:
    """Função principal"""
    print_section_header("Push do Prompt Otimizado")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    _ensure_langsmith_compat_env()

    prompt_yaml = load_yaml(str(PROMPT_FILE))
    if not prompt_yaml:
        print(f"Nao foi possivel carregar o arquivo: {PROMPT_FILE}")
        return 1

    prompt_data = prompt_yaml.get(PROMPT_KEY)
    if prompt_data is None:
        print(f"Chave '{PROMPT_KEY}' nao encontrada em {PROMPT_FILE}.")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("Prompt invalido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    prompt_name = f"{username}/{PROMPT_SLUG}"

    print(f"Arquivo: {PROMPT_FILE}")
    print(f"Destino: {prompt_name}")

    success = push_prompt_to_langsmith(prompt_name, prompt_data)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
