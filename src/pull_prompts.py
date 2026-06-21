"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from langchain import hub

from utils import check_env_vars, print_section_header, save_yaml

load_dotenv()

PROMPT_HUB_NAME = "leonanluppi/bug_to_user_story_v1"
PROMPT_KEY = "bug_to_user_story_v1"
REFERENCE_PROMPT_PATH = Path("prompts/bug_to_user_story_v1.yml")
OUTPUT_PROMPT_PATH = Path("prompts/bug_to_user_story_v1.yml")


def _ensure_langsmith_compat_env() -> None:
    """Mantem compatibilidade com clientes que ainda usam variaveis LANGCHAIN_*."""
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    if langsmith_api_key and not os.getenv("LANGCHAIN_API_KEY"):
        os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key

    langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")
    if langsmith_endpoint and not os.getenv("LANGCHAIN_ENDPOINT"):
        os.environ["LANGCHAIN_ENDPOINT"] = langsmith_endpoint


def _load_reference_metadata() -> dict:
    """Carrega os metadados do YAML de referencia para preservar valores e ordem."""
    default_metadata = {
        "description": "Prompt para converter relatos de bugs em User Stories",
        "version": "v1",
        "created_at": "2025-01-15",
        "tags": ["bug-analysis", "user-story", "product-management"],
    }

    try:
        with open(REFERENCE_PROMPT_PATH, "r", encoding="utf-8") as file:
            reference_data = yaml.safe_load(file) or {}
    except FileNotFoundError:
        return default_metadata

    prompt_data = reference_data.get(PROMPT_KEY, {})
    return {
        "description": prompt_data.get("description", default_metadata["description"]),
        "version": prompt_data.get("version", default_metadata["version"]),
        "created_at": prompt_data.get("created_at", default_metadata["created_at"]),
        "tags": prompt_data.get("tags", default_metadata["tags"]),
    }


def _message_role(message) -> str:
    """Infere o papel da mensagem retornada pelo LangChain."""
    if hasattr(message, "type"):
        return str(message.type).lower()

    class_name = message.__class__.__name__.lower()
    if "system" in class_name:
        return "system"
    if "human" in class_name or "user" in class_name:
        return "human"

    return class_name


def _message_template(message) -> str:
    """Extrai o texto de mensagens e templates do LangChain."""
    if hasattr(message, "prompt") and hasattr(message.prompt, "template"):
        return message.prompt.template

    if hasattr(message, "template"):
        return message.template

    if hasattr(message, "content"):
        return message.content

    raise ValueError(f"Nao foi possivel extrair texto da mensagem: {message!r}")


def _extract_prompt_parts(prompt) -> tuple[str, str]:
    """Extrai system_prompt e user_prompt do objeto retornado pelo Hub."""
    messages = getattr(prompt, "messages", None)
    if not messages:
        template = getattr(prompt, "template", None)
        if template:
            return template, "{bug_report}"
        raise ValueError("O prompt retornado nao possui mensagens nem template.")

    system_prompt = None
    user_prompt = None

    for message in messages:
        role = _message_role(message)
        template = _message_template(message)

        if role == "system" and system_prompt is None:
            system_prompt = template
        elif role in {"human", "user"} and user_prompt is None:
            user_prompt = template

    if not system_prompt:
        raise ValueError("Nao foi encontrada uma mensagem system no prompt baixado.")

    return system_prompt, user_prompt or "{bug_report}"


def _save_prompt_yaml(prompt_data: dict, file_path: Path) -> bool:
    """Salva o prompt em YAML usando o helper padrao do projeto."""
    return save_yaml({PROMPT_KEY: prompt_data}, str(file_path))


def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt v1 no LangSmith Hub e salva uma copia local em YAML.

    Returns:
        True se sucesso, False caso contrario.
    """
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return False

    _ensure_langsmith_compat_env()

    try:
        print(f"Puxando prompt do Hub: {PROMPT_HUB_NAME}")
        prompt = hub.pull(PROMPT_HUB_NAME)

        system_prompt, user_prompt = _extract_prompt_parts(prompt)
        metadata = _load_reference_metadata()

        prompt_data = {
            "description": metadata["description"],
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": metadata["version"],
            "created_at": metadata["created_at"],
            "tags": metadata["tags"],
        }

        if not _save_prompt_yaml(prompt_data, OUTPUT_PROMPT_PATH):
            return False

        print(f"Prompt salvo em: {OUTPUT_PROMPT_PATH}")
        return True
    except Exception as error:
        print(f"Erro ao fazer pull do prompt: {error}")
        return False


def main() -> int:
    """Função principal"""
    print_section_header("Pull do Prompt LangSmith")

    success = pull_prompts_from_langsmith()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
