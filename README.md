# 🔑 Archon Lens — KeyForge Deck Analyzer

> 🇧🇷 [Português](#-português) · 🇺🇸 [English](#-english)

---

## 🇧🇷 Português

App web construído com [Streamlit](https://streamlit.io) que consome a API pública do
[Decks of KeyForge (DoK)](https://decksofkeyforge.com) e exibe uma análise completa da sua coleção.

### ✨ Funcionalidades

| Aba | O que mostra |
|-----|-------------|
| 🏰 **Alliance Optimizer** | Melhores combinações de 3 pods por expansão e estratégia |
| 🏠 **Análise por Casa** | AERC detalhado por pod (cada casa de cada deck) |
| 📊 **Resumo** | Métricas gerais, decks por expansão, frequência de casas |
| 🃏 **Meus Decks** | Tabela completa com filtros, ~50 colunas, download CSV/Excel |
| 📈 **Gráficos** | Distribuição SAS, decks por expansão, frequência de casas, SAS×AERC |

### 🚀 Rodando localmente

```bash
# 1. Clone o repositório
git clone https://github.com/romariopaixao/archon-lens.git
cd archon-lens

# 2. Crie e ative um ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode o app
streamlit run app.py
```

O browser abre automaticamente em `http://localhost:8501`.

### 🔑 Como obter sua API Key

Gere sua chave em [decksofkeyforge.com/about/sellers-and-devs](https://decksofkeyforge.com/about/sellers-and-devs):

1. Faça login no DoK
2. Role até o final da página
3. Clique em **"Generate API Key"**

> Certifique-se de que seus decks estão marcados com **"I own this deck"** no DoK antes de usar.

### 🔒 Privacidade

Sua chave **nunca é salva** — ela existe apenas na memória da sessão ativa e desaparece ao fechar a aba.
Este projeto é open-source: você pode auditar o código em `app.py` e confirmar isso.

### 🏰 Lógica de ranqueamento do Alliance Optimizer

O score de cada combinação de 3 pods é calculado somando as métricas AERC de cada pod, multiplicadas por pesos que variam conforme a estratégia escolhida:

```
score = Σ (métrica_do_pod × peso_da_estratégia)
```

| Estratégia | Métricas e pesos |
|---|---|
| **AERC Geral** | AERC do pod × 1,0 |
| **Control** | Amber Control × 1,5 + Creature Control × 1,5 + Disruption × 1,0 |
| **Rush** | Expected Amber × 2,0 + Efficiency × 1,0 |
| **Anti-criatura** | Creature Control × 2,0 + Creature Protection × 1,0 |
| **Anti-artefato** | Artifact Control × 2,0 + Disruption × 1,0 |

> Os pesos maiores (2,0) indicam a métrica principal da estratégia; os menores (1,0) são métricas de suporte.  
> A Restricted List é aplicada automaticamente — combinações que violam as regras vigentes são descartadas antes do ranqueamento.

---

## 🇺🇸 English

A web app built with [Streamlit](https://streamlit.io) that connects to the public
[Decks of KeyForge (DoK)](https://decksofkeyforge.com) API and delivers a full analysis of your collection.

### ✨ Features

| Tab | What it shows |
|-----|--------------|
| 🏰 **Alliance Optimizer** | Best 3-pod combinations per expansion and strategy |
| 🏠 **House Analysis** | Detailed AERC breakdown per pod (each house of each deck) |
| 📊 **Overview** | General metrics, decks per expansion, house frequency |
| 🃏 **My Decks** | Full table with filters, ~50 columns, CSV/Excel download |
| 📈 **Charts** | SAS distribution, decks per expansion, house frequency, SAS×AERC scatter |

### 🚀 Running locally

```bash
# 1. Clone the repository
git clone https://github.com/romariopaixao/archon-lens.git
cd archon-lens

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The browser opens automatically at `http://localhost:8501`.

### 🔑 Getting your API Key

Generate your key at [decksofkeyforge.com/about/sellers-and-devs](https://decksofkeyforge.com/about/sellers-and-devs):

1. Log in to DoK
2. Scroll to the bottom of the page
3. Click **"Generate API Key"**

> Make sure your decks are marked as **"I own this deck"** on DoK before using the app.

### 🔒 Privacy

Your API key is **never stored** — it lives only in the active session memory and disappears when you close the tab.
This project is open-source: you can audit the code in `app.py` to verify this.

### 🏰 Alliance Optimizer — Ranking logic

Each 3-pod combination is scored by summing the AERC metrics of every pod, multiplied by strategy-specific weights:

```
score = Σ (pod_metric × strategy_weight)
```

| Strategy | Metrics and weights |
|---|---|
| **AERC General** | Pod AERC × 1.0 |
| **Control** | Amber Control × 1.5 + Creature Control × 1.5 + Disruption × 1.0 |
| **Rush** | Expected Amber × 2.0 + Efficiency × 1.0 |
| **Anti-creature** | Creature Control × 2.0 + Creature Protection × 1.0 |
| **Anti-artifact** | Artifact Control × 2.0 + Disruption × 1.0 |

> Higher weights (2.0) mark the primary metric for that strategy; lower weights (1.0) are supporting metrics.  
> The Restricted List is enforced automatically — combinations that break the current rules are discarded before ranking.

### 🌐 Free deployment on Streamlit Community Cloud

1. Fork or push this repo to your GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"** → select this repository → `app.py`
4. Click **Deploy**

You'll get a public link at `https://your-username-archon-lens.streamlit.app`.

---

## 📦 Project structure

```
archon-lens/
├── app.py              # Streamlit app (all logic)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable example
├── .gitignore          # Files not to commit
└── README.md           # This file
```

## 🙏 Credits

- API by [Decks of KeyForge](https://decksofkeyforge.com) — consider supporting them on [Patreon](https://www.patreon.com/decksofkeyforge)
- KeyForge is a registered trademark of Ghost Galaxy / FFG
