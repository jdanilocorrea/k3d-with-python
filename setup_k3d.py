import subprocess
import time
import sys
import os

# Configuração do Cluster
CLUSTER_CONFIG = {
    "cluster_name": "devops-lab",
    "servers": 1,
    "agents": 2,
    "metallb_range": "172.18.255.200-172.18.255.250"
}

def run_command(command, description, ignore_error=False):
    """Executa comandos shell com feedback claro."""
    print(f"🛠️  {description}...")
    try:
        result = subprocess.run(
            command, check=not ignore_error, capture_output=True, text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr.lower():
            print(f"   ℹ️  Aviso: Recurso já existe. Continuando...")
            return None
        print(f"   ❌ Erro crítico em '{description}': {e.stderr.strip()}")
        sys.exit(1)

def wait_for_deployment(namespace, deployment_name, timeout="300s"):
    """Usa o comando nativo 'kubectl wait' para garantir prontidão."""
    print(f"⏳ Aguardando deployment '{deployment_name}' em '{namespace}' ficar disponível...")
    cmd = [
        "kubectl", "wait", 
        f"--for=condition=available", 
        f"deployment/{deployment_name}", 
        "-n", namespace, 
        f"--timeout={timeout}"
    ]
    run_command(cmd, f"Verificando disponibilidade de {deployment_name}")

def setup():
    # 1. Gerenciamento do Cluster
    # Usamos ignore_error=True aqui para que o script não pare se o cluster já existir
    run_command([
        "k3d", "cluster", "create", CLUSTER_CONFIG["cluster_name"],
        "--servers", str(CLUSTER_CONFIG["servers"]),
        "--agents", str(CLUSTER_CONFIG["agents"]),
        "--port", "8080:80@loadbalancer",
        "--k3s-arg", "--disable=traefik@server:*",
        "--k3s-arg", "--disable=servicelb@server:*",
        "--wait"
    ], "Provisionando Cluster K3D", ignore_error=True)

    # 2. Atualização de Repositórios
    repos = {
        "cilium": "https://helm.cilium.io/",
        "metallb": "https://metallb.github.io/metallb",
        "prometheus-community": "https://prometheus-community.github.io/helm-charts",
        "ingress-nginx": "https://kubernetes.github.io/ingress-nginx"
    }
    for name, url in repos.items():
        run_command(["helm", "repo", "add", name, url], f"Adicionando repo {name}", ignore_error=True)
    run_command(["helm", "repo", "update"], "Sincronizando Helm Repos")

    # 3. Cilium (Network)
    run_command([
        "helm", "upgrade", "--install", "cilium", "cilium/cilium", 
        "--namespace", "kube-system"
    ], "Instalando Cilium CNI")
    # O Cilium não usa Deployment padrão, esperamos o DaemonSet ou apenas um pequeno delay
    time.sleep(20)

    # 4. MetalLB (LoadBalancer)
    run_command([
        "helm", "upgrade", "--install", "metallb", "metallb/metallb", 
        "--namespace", "metallb-system", "--create-namespace"
    ], "Instalando MetalLB")
    
    # ESPERA NATIVA: Isso substitui o loop de segundos que estava travando
    wait_for_deployment("metallb-system", "metallb-controller")
    
    print("💡 Estabilizando Webhook Admission (15s)...")
    time.sleep(15)

    metallb_config = f"""
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: first-pool
  namespace: metallb-system
spec:
  addresses:
  - {CLUSTER_CONFIG['metallb_range']}
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: l2-adv
  namespace: metallb-system
"""
    with open("metallb-conf.yaml", "w") as f:
        f.write(metallb_config)
    
    run_command(["kubectl", "apply", "-f", "metallb-conf.yaml"], "Aplicando L2 Advertisement e IP Pool")

    # 5. Nginx Ingress
    run_command([
        "helm", "upgrade", "--install", "ingress-nginx", "ingress-nginx/ingress-nginx", 
        "--namespace", "ingress-nginx", "--create-namespace"
    ], "Instalando NGINX Ingress Controller")

    # 6. Observabilidade
    run_command([
        "helm", "upgrade", "--install", "monitoring", "prometheus-community/kube-prometheus-stack",
        "--namespace", "monitoring", "--create-namespace"
    ], "Instalando Stack Prometheus/Grafana")

    print("\n" + "="*60)
    print("✅ AMBIENTE PRONTO E OPERACIONAL!")
    print("="*60)
    print(f"Cluster K3D: {CLUSTER_CONFIG['cluster_name']}")
    print("Verifique o IP Externo: kubectl get svc -n ingress-nginx")
    print("Acesso Grafana: localhost:3000 (após port-forward)")
    print("="*60)

if __name__ == "__main__":
    setup()