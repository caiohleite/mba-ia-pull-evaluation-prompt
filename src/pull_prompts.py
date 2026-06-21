"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1_download2.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = Path("prompts/bug_to_user_story_v1_download2.yml")


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt do LangSmith Hub e salva em YAML.
    """

    print_section_header("Pull Prompt do LangSmith")

    client = Client()

    print(f"Obtendo prompt: {PROMPT_NAME}")

    prompt = client.pull_prompt(PROMPT_NAME)

    print(f"✓ Prompt encontrado")
    print(f"✓ Tipo: {prompt.__class__.__name__}")

    #
    # Metadados do Hub
    #
    metadata = {
        "owner": prompt.metadata.get("lc_hub_owner"),
        "repo": prompt.metadata.get("lc_hub_repo"),
        "commit_hash": prompt.metadata.get("lc_hub_commit_hash"),
    }

    #
    # Mensagens (System/Human/etc.)
    #
    messages = []

    for msg in prompt.messages:
        class_name = msg.__class__.__name__

        if class_name.startswith("System"):
            role = "system"
        elif class_name.startswith("Human"):
            role = "human"
        elif class_name.startswith("AI"):
            role = "ai"
        else:
            role = class_name

        message_data = {
            "role": role,
            "message_type": class_name,
            "template": msg.prompt.template,
            "input_variables": msg.prompt.input_variables,
        }

        messages.append(message_data)

    #
    # Estrutura final exportada
    #
    prompt_data = {
        "prompt_name": PROMPT_NAME,
        "prompt_type": prompt.__class__.__name__,
        "metadata": metadata,
        "input_variables": prompt.input_variables,
        "messages": messages,
        "langchain_json": prompt.to_json(),
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    save_yaml(prompt_data, OUTPUT_FILE)

    print(f"✓ Prompt salvo em: {OUTPUT_FILE}")

    return prompt_data


def main():
    """Função principal"""

    check_env_vars(
        [
            "LANGSMITH_API_KEY",
        ]
    )

    try:
        pull_prompts_from_langsmith()

        print_section_header("Concluído")
        print("Pull realizado com sucesso.")

        return 0

    except Exception as exc:
        print(f"\nErro ao realizar pull do prompt:")
        print(f"{type(exc).__name__}: {exc}")

        return 1


if __name__ == "__main__":
    sys.exit(main())