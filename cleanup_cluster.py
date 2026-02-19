import subprocess
import os
import sys

# Deve ser o mesmo nome usado no setup_cluster.py
CLUSTER_NAME = "devops-lab"
TEMP_FILES = ["metallb-conf.yaml"]

def run_command(command, description, ignore_error=False):
    """Executa comandos shell e fornece feedback."""
    print(f"🧹 {description}...")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"   ✅ Concluído.")
    except subprocess.CalledProcessError as e:
        if not ignore_error:
            print(f"   ⚠️  Aviso: {e.stderr.strip()}")
        else:
            print(f"   ℹ️  Recurso já não existia.")

def cleanup():
    print(f"🔥 Iniciando destruição do ambiente: {CLUSTER_NAME}\n")

    # 1. Deletar o cluster k3d (isso remove containers, redes e volumes do Docker)
    run_command(
        ["k3d", "cluster", "delete", CLUSTER_NAME], 
        f"Removendo cluster k3d '{CLUSTER_NAME}'",
        ignore_error=True
    )

    # 2. Remover arquivos locais gerados pelo Python
    print("📂 Limpando arquivos locais...")
    for file in TEMP_FILES:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"   ✅ Arquivo '{file}' removido.")
            except Exception as e:
                print(f"   ❌ Erro ao remover '{file}': {e}")
        else:
            print(f"   ℹ️  Arquivo '{file}' não encontrado (já limpo).")

    # 3. Limpar contextos órfãos do kubectl (opcional, mas boa prática)
    run_command(
        ["kubectl", "config", "delete-context", f"k3d-{CLUSTER_NAME}"],
        "Limpando contexto do kubectl",
        ignore_error=True
    )

if __name__ == "__main__":
    # Confirmação de segurança
    confirm = input(f"⚠️  VOCÊ TEM CERTEZA? Isso destruirá o cluster '{CLUSTER_NAME}' [s/N]: ")
    if confirm.lower() == 's':
        cleanup()
        print("\n✨ Tudo limpo! Seu ambiente está pronto para um novo setup.")
    else:
        print("\n❌ Operação cancelada pelo usuário.")