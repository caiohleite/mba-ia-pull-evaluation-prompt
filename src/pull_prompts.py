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
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith():
    """Faz pull de um prompt do LangSmith e salva localmente."""
    prompt_name = "leonanluppi/bug_to_user_story_v1"
    output_path = "prompts/bug_to_user_story_v1_download2.yml"
    
    print_section_header("Buscando prompt no LangSmith")
    print(f"Fazendo pull de '{prompt_name}'...")
    
    try:
        # Client() garante que as credenciais do ambiente sejam checadas
        from langsmith import Client
        Client()
        
        # Faz o pull do prompt
        prompt = hub.pull(prompt_name)
        
        # Salva o prompt usando serialização nativa (dicionário do langchain) 
        # A instrução fala para usar 'serialização nativa do LangChain'
        prompt_dict = prompt.dict()
        
        if save_yaml(prompt_dict, output_path):
            print(f"✅ Prompt salvo com sucesso em: {output_path}")
        else:
            print("❌ Falha ao salvar o prompt.")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)
def main():
    """Função principal"""
    # Verifica variáveis de ambiente necessárias
    required_vars = ["LANGSMITH_API_KEY"]
    if not check_env_vars(required_vars):
        sys.exit(1)
        
    pull_prompts_from_langsmith()
    return 0
if __name__ == "__main__":
    sys.exit(main())
