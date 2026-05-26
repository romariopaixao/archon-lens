# 🔑 KeyForge Deck Analyzer

App web construído com [Streamlit](https://streamlit.io) que consome a API pública do
[Decks of KeyForge (DoK)](https://decksofkeyforge.com) e exibe uma análise completa da sua coleção.

## ✨ Funcionalidades

| Aba | O que mostra |
|-----|-------------|
| 📊 **Resumo** | Métricas gerais, decks por expansão, frequência de casas |
| 🃏 **Meus Decks** | Tabela completa com filtros, ~50 colunas, download CSV/Excel |
| 🏠 **Análise por Casa** | AERC detalhado por pod (cada casa de cada deck) |
| 🏰 **Alliance Optimizer** | Melhores combinações de 3 pods por expansão e estratégia |
| 📈 **Gráficos** | Distribuição SAS, decks por expansão, frequência de casas, SAS×AERC |

## 🚀 Rodando localmente

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/keyforge-streamlit.git
cd keyforge-streamlit

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

## 🔑 API Key

Gere sua chave em [decksofkeyforge.com/about/sellers-and-devs](https://decksofkeyforge.com/about/sellers-and-devs):

1. Faça login no DoK
2. Role até o final da página
3. Clique em **"Generate API Key"**

Certifique-se de que seus decks estão marcados com **"I own this deck"** no DoK antes de rodar.

## 🔒 Segurança da API Key

> Sua chave **nunca é salva** — ela existe apenas na memória da sessão ativa para fazer as
> requisições ao DoK e some ao fechar a aba.  
> Este projeto é open-source: você pode auditar o código em `app.py` e confirmar isso.

## 🌐 Deploy gratuito no Streamlit Community Cloud

1. Faça um fork/push deste repo para o seu GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Clique em **"New app"** → selecione este repositório → `app.py`
4. Clique em **Deploy**

Pronto — você terá um link público `https://seu-usuario-keyforge-streamlit.streamlit.app`.

## 📦 Estrutura do projeto

```
keyforge_streamlit/
├── app.py              # Aplicação Streamlit (toda a lógica)
├── requirements.txt    # Dependências Python
├── .env.example        # Exemplo de variáveis de ambiente
├── .gitignore          # Arquivos a não commitar
└── README.md           # Este arquivo
```

## 🙏 Créditos

- API por [Decks of KeyForge](https://decksofkeyforge.com) — considere apoiar no [Patreon](https://www.patreon.com/decksofkeyforge)
- KeyForge é marca registrada da Ghost Galaxy / FFG
