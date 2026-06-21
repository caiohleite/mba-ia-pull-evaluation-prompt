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
        # Usa o Client recomendado do LangSmith em vez do langchain.hub
        from langsmith import Client
        client = Client()
        
        # Faz o pull do prompt pelo client
        prompt = client.pull_prompt(prompt_name)
        
        # Serialização nativa inicial
        prompt_dict = prompt.dict()
        
        # O método dict() nativo muitas vezes não serializa os templates aninhados (retorna [{}, {}]).
        # Portanto, precisamos extrair os textos do system e user prompt explicitamente:
        if hasattr(prompt, 'messages'):
            system_prompt = ""
            user_prompt = ""
            
            for msg in prompt.messages:
                msg_type = msg.__class__.__name__
                # Extrai o template de texto de cada mensagem
                template_text = msg.prompt.template if hasattr(msg, 'prompt') else ""
                
                if msg_type == 'SystemMessagePromptTemplate':
                    system_prompt = template_text
                elif msg_type == 'HumanMessagePromptTemplate':
                    user_prompt = template_text
            
            # Reconstrói a estrutura no padrão que o projeto espera (similar ao bug_to_user_story_v1.yml)
            custom_prompt_data = {
                prompt_name.split("/")[-1]: {
                    "description": "Prompt extraído do LangSmith",
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "version": "v1",
                    "metadata": prompt_dict.get("metadata", {})
                }
            }
            # Substituímos o dict padrão pelo nosso customizado para ficar com o formato correto
            prompt_dict = custom_prompt_data
        
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
