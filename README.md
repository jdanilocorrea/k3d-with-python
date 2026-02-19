
# 🚀 K3d DevOps Lab: Cluster Local Automatizado com Python

Este projeto automatiza o provisionamento de um cluster **Kubernetes** local utilizando **k3d** (K3s in Docker). O objetivo é fornecer um ambiente de desenvolvimento idêntico à produção, incluindo CNI avançada, LoadBalancer de Camada 2, Ingress Controller e uma stack completa de observabilidade.

---

## 🏗️ Arquitetura da Stack
O cluster é configurado com as seguintes tecnologias:

| Componente | Tecnologia | Descrição |
| :--- | :--- | :--- |
| **Cluster Engine** | k3d | 1 Server + 2 Agents |
| **CNI (Network)** | Cilium | Via eBPF (substituindo o Kube-Proxy) |
| **LoadBalancer** | MetalLB | Modo Layer 2 |
| **Ingress Controller** | NGINX | Roteamento de tráfego externo |
| **Observabilidade** | Prometheus & Grafana | Kube-Prometheus-Stack |

---

## 📋 Pré-requisitos
Antes de iniciar, certifique-se de ter instalado em sua máquina:

* **Docker** (Engine rodando)
* **k3d CLI**:
  ```bash
  curl -s [https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh](https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh) | TAG=v5.6.0 bash
  

> \[!NOTE\] O script gerencia as dependências e aguarda até que os webhooks de validação do **MetalLB** estejam prontos (`kubectl wait`) antes de aplicar as configurações de rede.

### 2\. Acesso aos Serviços

- **NGINX Ingress:** O IP do LoadBalancer será atribuído no range `172.18.255.200` - `172.18.255.250`.
    
- **Grafana Dashboards:**
    
    Bash
    
    ```
    kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
    ```
    
    - **URL:** `http://localhost:3000`
        
    - **Usuário:** `admin`
        
    - **Senha:** `prom-operator`
        

* * *

## 🧹 Limpeza

Para destruir o cluster e remover todos os arquivos temporários, garantindo que não haja consumo residual de recursos:

Bash

```
python cleanup_cluster.py
```

* * *

## 🛠️ Detalhes Técnicos do Script Python

O script `setup_k3d.py` utiliza as seguintes boas práticas de DevOps:

- **Idempotência:** Utiliza `helm upgrade --install` para permitir múltiplas execuções sem falhas ou duplicação.
    
- **Health Checks:** Implementa verificações de prontidão para garantir que um componente só seja configurado após o seu Pod estar em estado `Ready`.
    
- **Gerenciamento Dinâmico de YAML:** Gera o arquivo `metallb-conf.yaml` baseado nas configurações reais da rede Docker do host.
    

* * *

## ☁️ Notas de Produção

Embora este seja um ambiente local, a configuração do **Cilium** e do **NGINX** segue padrões utilizados em clouds como AWS (EKS) e GCP (GKE). Em um ambiente cloud real, o **MetalLB** seria substituído pelo Cloud Load Balancer nativo (NLB/ALB).