"""
🔑 KeyForge Deck Analyzer — Streamlit App
Consome a API pública do Decks of KeyForge e exibe análise completa da coleção.
"""

import io
import json
import time
from collections import Counter
from datetime import datetime
from itertools import combinations
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

# ──────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────

BASE_URL = "https://decksofkeyforge.com"

EXPANSION_ABBR: dict[str, str] = {
    "CALL_OF_THE_ARCHONS": "CotA",
    "AGE_OF_ASCENSION": "AoA",
    "WORLDS_COLLIDE": "WC",
    "MASS_MUTATION": "MM",
    "DARK_TIDINGS": "DT",
    "WINDS_OF_EXCHANGE": "WoE",
    "UNCHAINED_2022": "U22",
    "VAULT_MASTERS_2023": "VM23",
    "GRIM_REMINDERS": "GR",
    "MENAGERIE_2024": "M24",
    "VAULT_MASTERS_2024": "VM24",
    "AEMBER_SKIES": "AS",
    "TOKENS_OF_CHANGE": "ToC",
    "MORE_MUTATION": "MoM",
    "MARTIAN_CIVIL_WAR": "MCW",
    "DISCOVERY": "DIS",
}

AERC_COMPONENTS = [
    "expectedAmber", "amberControl",
    "creatureControl", "artifactControl",
    "effectivePower", "efficiency",
    "disruption", "recursion",
    "creatureProtection", "other",
]

STRATEGIES: dict[str, dict] = {
    "AERC Geral":    {"pod_aerc": 1.0},
    "Control":       {"sum_amberControl": 1.5, "sum_creatureControl": 1.5, "sum_disruption": 1.0},
    "Rush":          {"sum_expectedAmber": 2.0, "sum_efficiency": 1.0},
    "Anti-criatura": {"sum_creatureControl": 2.0, "sum_creatureProtection": 1.0},
    "Anti-artefato": {"sum_artifactControl": 2.0, "sum_disruption": 1.0},
}

RESTRICTED_LIST: dict[str, tuple] = {
    "Library Access":     (1, ["CALL_OF_THE_ARCHONS", "AGE_OF_ASCENSION", "WORLDS_COLLIDE"]),
    "Martian Generosity": (1, ["WORLDS_COLLIDE"]),
    "Restringuntus":      (1, ["CALL_OF_THE_ARCHONS", "AGE_OF_ASCENSION"]),
    "Legionary Trainer":  (3, ["WINDS_OF_EXCHANGE"]),
    "Befuddle":           (2, ["WINDS_OF_EXCHANGE"]),
    "Reiteration":        (1, ["PROPHETIC_VISIONS"]),
    "Strategic Feint":    (1, ["PROPHETIC_VISIONS"]),
}

# ──────────────────────────────────────────────────────────────
# Funções de pipeline (API + processamento)
# ──────────────────────────────────────────────────────────────

def make_headers(api_key: str) -> dict:
    return {"Api-Key": api_key.strip(), "Accept": "application/json"}


def fetch_my_decks(headers: dict) -> list[dict]:
    resp = requests.get(f"{BASE_URL}/public-api/v1/my-decks", headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        for key in ("decks", "myDecks", "data"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
    if not isinstance(data, list):
        raise RuntimeError(f"Formato inesperado da API: {type(data)}")
    decks = []
    for item in data:
        if isinstance(item, dict) and "deck" in item and isinstance(item["deck"], dict):
            decks.append(item["deck"])
        else:
            decks.append(item)
    return decks


def fetch_deck_details(keyforge_id: str, headers: dict, max_retries: int = 3) -> dict | None:
    url = f"{BASE_URL}/public-api/v3/decks/{keyforge_id}"
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException:
            if attempt == max_retries - 1:
                return None
            time.sleep(2 ** attempt)
    return None


def fetch_all_cards(headers: dict) -> list[dict]:
    resp = requests.get(f"{BASE_URL}/public-api/v1/cards", headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.json()


def flatten_deck(deck: dict) -> dict:
    row: dict[str, Any] = {}
    for k, v in deck.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            row[k] = v
    if "expansion" in row:
        row["expansionAbbr"] = EXPANSION_ABBR.get(row["expansion"], row["expansion"])
    houses_and_cards = deck.get("housesAndCards") or []
    if isinstance(houses_and_cards, list):
        houses = [h.get("house") for h in houses_and_cards if isinstance(h, dict) and h.get("house")]
        row["houses"] = ", ".join(houses) if houses else None
        for i, h in enumerate(houses[:3], start=1):
            row[f"house_{i}"] = h
    all_cards: list[str] = []
    for h in houses_and_cards:
        if isinstance(h, dict):
            for c in h.get("cards", []) or []:
                if isinstance(c, dict) and c.get("cardTitle"):
                    all_cards.append(c["cardTitle"])
                elif isinstance(c, str):
                    all_cards.append(c)
    if all_cards:
        row["card_count"] = len(all_cards)
        row["cards_list"] = " | ".join(all_cards)
    if "keyforgeId" in row:
        row["dok_url"] = f"https://decksofkeyforge.com/decks/{row['keyforgeId']}"
        row["masterVault_url"] = f"https://www.keyforgegame.com/deck-details/{row['keyforgeId']}"
    return row


def build_decks_df(detailed_decks: list[dict]) -> pd.DataFrame:
    flat_rows = [flatten_deck(d) for d in detailed_decks]
    df = pd.DataFrame(flat_rows)
    priority_cols = [
        "name", "expansionAbbr", "expansion", "houses", "house_1", "house_2", "house_3",
        "sasRating", "synergyRating", "antisynergyRating", "aercScore",
        "amberControl", "expectedAmber", "artifactControl", "creatureControl",
        "efficiency", "recursion", "disruption", "creatureProtection",
        "other", "effectivePower",
        "rawAmber", "creatureCount", "actionCount", "artifactCount", "upgradeCount",
        "powerLevel", "chains", "wins", "losses",
        "keyforgeId", "dok_url", "masterVault_url",
    ]
    ordered = [c for c in priority_cols if c in df.columns] + \
              [c for c in df.columns if c not in priority_cols]
    return df[ordered]


def _get_aerc(card_obj: dict) -> dict:
    eci = (card_obj or {}).get("extraCardInfo") or {}
    out = {k: float(eci.get(k) or 0) for k in AERC_COMPONENTS}
    out["aercScoreBase"] = float(eci.get("aercScoreAverage") or 0)
    return out


def build_pods_df(detailed_decks: list[dict], all_cards: list[dict]) -> pd.DataFrame:
    cards_by_title = {}
    for c in all_cards:
        title = c.get("cardTitle")
        if title and title not in cards_by_title:
            cards_by_title[title] = c

    pod_rows = []
    for deck in detailed_decks:
        deck_meta = {
            "deck_name":    deck.get("name"),
            "expansion":    deck.get("expansion"),
            "expansionAbbr": EXPANSION_ABBR.get(deck.get("expansion", ""), deck.get("expansion")),
            "keyforgeId":   deck.get("keyforgeId"),
            "deck_sas":     deck.get("sasRating"),
            "deck_aerc":    deck.get("aercScore"),
            "dok_url":      f"https://decksofkeyforge.com/decks/{deck.get('keyforgeId')}",
        }
        for hac in deck.get("housesAndCards") or []:
            house = hac.get("house")
            cards_in_house = hac.get("cards") or []

            agg = {k: 0.0 for k in AERC_COMPONENTS}
            agg["aercScoreBase"] = 0.0
            type_counts = {"Creature": 0, "Action": 0, "Artifact": 0, "Upgrade": 0}
            raw_amber = total_power = total_armor = 0
            enh_amber = enh_draw = enh_damage = enh_capture = 0
            rarities: Counter = Counter()
            has_legacy = has_maverick = has_anomaly = has_enhanced = False
            titles: list[str] = []

            for c_in_deck in cards_in_house:
                title = c_in_deck.get("cardTitle")
                if title:
                    titles.append(title)
                full = cards_by_title.get(title or "")
                if full is None:
                    continue
                ctype = (full.get("cardType") or "").capitalize()
                if ctype in type_counts:
                    type_counts[ctype] += 1
                raw_amber   += int(full.get("amber") or 0)
                total_power += int(full.get("power") or 0)
                total_armor += int(full.get("armor") or 0)
                rarities[full.get("rarity") or "?"] += 1
                for k, v in _get_aerc(full).items():
                    agg[k] += v
                enh_amber   += int(c_in_deck.get("bonusAember")  or 0)
                enh_draw    += int(c_in_deck.get("bonusDraw")    or 0)
                enh_damage  += int(c_in_deck.get("bonusDamage")  or 0)
                enh_capture += int(c_in_deck.get("bonusCapture") or 0)
                if c_in_deck.get("legacy"):   has_legacy = True
                if c_in_deck.get("maverick"): has_maverick = True
                if c_in_deck.get("anomaly"):  has_anomaly = True
                if c_in_deck.get("enhanced"): has_enhanced = True

            row = {
                **deck_meta, "house": house, "cards_in_house": len(cards_in_house),
                "creatures":  type_counts["Creature"],
                "actions":    type_counts["Action"],
                "artifacts":  type_counts["Artifact"],
                "upgrades":   type_counts["Upgrade"],
                "raw_amber": raw_amber, "total_power": total_power, "total_armor": total_armor,
                "enhancement_amber":   enh_amber,
                "enhancement_draw":    enh_draw,
                "enhancement_damage":  enh_damage,
                "enhancement_capture": enh_capture,
                **{f"sum_{k}": round(v, 3) for k, v in agg.items()},
                "raw_amber_with_enhancements": raw_amber + enh_amber,
                "has_legacy": has_legacy, "has_maverick": has_maverick,
                "has_anomaly": has_anomaly, "has_enhanced": has_enhanced,
                "commons":   rarities.get("Common", 0),
                "uncommons": rarities.get("Uncommon", 0),
                "rares":     rarities.get("Rare", 0),
                "specials":  rarities.get("Special", 0),
                "cards_list": " | ".join(titles),
            }
            pod_rows.append(row)

    df_pods = pd.DataFrame(pod_rows)

    # Renomeia sum_aercScoreBase → pod_aerc e calcula dimensional_score
    if "sum_aercScoreBase" in df_pods.columns:
        df_pods = df_pods.rename(columns={"sum_aercScoreBase": "pod_aerc"})
    sum_cols = [f"sum_{k}" for k in AERC_COMPONENTS if f"sum_{k}" in df_pods.columns]
    df_pods["dimensional_score"] = df_pods[sum_cols].sum(axis=1).round(2)

    front = [
        "deck_name", "expansionAbbr", "house",
        "pod_aerc", "dimensional_score",
        "sum_expectedAmber", "sum_amberControl",
        "sum_creatureControl", "sum_artifactControl",
        "sum_efficiency", "sum_disruption",
        "sum_effectivePower", "sum_creatureProtection",
        "sum_recursion", "sum_other",
    ]
    front_ok = [c for c in front if c in df_pods.columns]
    others   = [c for c in df_pods.columns if c not in front_ok]
    return df_pods[front_ok + others]


def _check_restricted(combo_pods: tuple) -> tuple[bool, str]:
    exp = combo_pods[0].get("expansion", "")
    counts: dict[str, int] = {}
    for pod in combo_pods:
        for title in (pod.get("cards_list") or "").split(" | "):
            title = title.strip()
            if title in RESTRICTED_LIST:
                max_c, sets = RESTRICTED_LIST[title]
                if exp in sets:
                    counts[title] = counts.get(title, 0) + 1
    if len(counts) > 1:
        return False, f"múltiplas restritas: {list(counts.keys())}"
    for card, cnt in counts.items():
        max_c, _ = RESTRICTED_LIST[card]
        if cnt > max_c:
            return False, f"{card}: {cnt}x > limite {max_c}"
    return True, "ok"


def generate_alliances(
    df_pods: pd.DataFrame,
    expansion_abbr: str,
    weights: dict,
    top_n: int = 10,
    enforce_restricted: bool = True,
) -> pd.DataFrame | None:
    pods = df_pods[df_pods["expansionAbbr"] == expansion_abbr].to_dict("records")
    if len(pods) < 3:
        return None
    candidates = []
    for combo in combinations(pods, 3):
        if len({p["house"] for p in combo}) < 3:
            continue
        if len({p["keyforgeId"] for p in combo}) < 3:
            continue
        if enforce_restricted and not _check_restricted(combo)[0]:
            continue
        sc = sorted(combo, key=lambda p: p["house"])
        score = sum(sum(p.get(col, 0) for p in sc) * w for col, w in weights.items())
        candidates.append({
            "score":          round(score, 2),
            "casa_1":         sc[0]["house"],
            "deck_1":         sc[0]["deck_name"],
            "casa_2":         sc[1]["house"],
            "deck_2":         sc[1]["deck_name"],
            "casa_3":         sc[2]["house"],
            "deck_3":         sc[2]["deck_name"],
            "pod_aerc_total": round(sum(p.get("pod_aerc", 0) for p in sc), 2),
            "amberControl":   round(sum(p.get("sum_amberControl", 0) for p in sc), 2),
            "expectedAmber":  round(sum(p.get("sum_expectedAmber", 0) for p in sc), 2),
            "creatureControl":round(sum(p.get("sum_creatureControl", 0) for p in sc), 2),
            "efficiency":     round(sum(p.get("sum_efficiency", 0) for p in sc), 2),
            "disruption":     round(sum(p.get("sum_disruption", 0) for p in sc), 2),
            "url_1": sc[0]["dok_url"],
            "url_2": sc[1]["dok_url"],
            "url_3": sc[2]["dok_url"],
        })
    if not candidates:
        return None
    return (
        pd.DataFrame(candidates)
        .sort_values("score", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


# ──────────────────────────────────────────────────────────────
# Helpers de download
# ──────────────────────────────────────────────────────────────

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    return buf.getvalue().encode("utf-8-sig")


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        ws = writer.sheets[sheet_name]
        ws.freeze_panes = "A2"
        for col in ws.columns:
            max_len = max(
                (len(str(c.value)) for c in col if c.value is not None), default=10
            )
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)
    return buf.getvalue()


def download_row(df: pd.DataFrame, file_stem: str, sheet_name: str) -> None:
    """Renderiza dois botões de download (CSV + Excel) lado a lado."""
    today = datetime.now().strftime("%Y%m%d")
    c1, c2 = st.columns(2)
    c1.download_button(
        "📥 Baixar CSV",
        data=to_csv_bytes(df),
        file_name=f"{file_stem}_{today}.csv",
        mime="text/csv",
        use_container_width=True,
    )
    c2.download_button(
        "📥 Baixar Excel",
        data=to_excel_bytes(df, sheet_name),
        file_name=f"{file_stem}_{today}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


# ──────────────────────────────────────────────────────────────
# Interface — página principal
# ──────────────────────────────────────────────────────────────

def _render_results(df: pd.DataFrame, df_pods: pd.DataFrame) -> None:
    """Renderiza todas as abas de resultado. Chamado sempre que os dados já estão em memória."""

    col_info, col_reload = st.columns([4, 1])
    with col_info:
        st.success(f"🎉 **{len(df)} decks** carregados — interaja à vontade, sem recarregar!")
    with col_reload:
        if st.button("🔄 Nova consulta", use_container_width=True, help="Limpa os dados e volta ao formulário"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    tab_alliance, tab_pods, tab_resumo, tab_decks, tab_graficos = st.tabs([
        "🏰 Alliance Optimizer",
        "🏠 Análise por Casa",
        "📊 Resumo",
        "🃏 Meus Decks",
        "📈 Gráficos",
    ])

    # ── TAB 1: Alliance Optimizer ───────────────────────────
    with tab_alliance:
        st.subheader("🏰 Alliance Optimizer")
        st.markdown("""
        Encontra as melhores combinações de **3 pods de decks distintos da mesma expansão**
        para montar um Alliance Deck competitivo. A Restricted List vigente já é aplicada automaticamente.
        """)

        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            available_exps = sorted(df_pods["expansionAbbr"].dropna().unique())
            alliance_exp = st.selectbox("Expansão", available_exps, key="ally_exp")
        with ac2:
            alliance_strat = st.selectbox("Estratégia", list(STRATEGIES.keys()), key="ally_strat")
        with ac3:
            top_n = st.slider("Top N combinações", min_value=1, max_value=20, value=5, key="ally_topn")

        if st.button("🔍 Calcular melhores Alliances", use_container_width=True, key="btn_alliance"):
            with st.spinner(f"Calculando combinações para {alliance_exp}..."):
                result = generate_alliances(
                    df_pods,
                    expansion_abbr=alliance_exp,
                    weights=STRATEGIES[alliance_strat],
                    top_n=top_n,
                )
            # Guarda resultado no estado para persistir entre reruns
            st.session_state["alliance_result"]  = result
            st.session_state["alliance_exp_used"]   = alliance_exp
            st.session_state["alliance_strat_used"] = alliance_strat

        # Exibe o resultado guardado (persiste mesmo ao mudar filtros)
        result       = st.session_state.get("alliance_result")
        exp_used     = st.session_state.get("alliance_exp_used", "")
        strat_used   = st.session_state.get("alliance_strat_used", "")

        if result is not None:
            if result.empty:
                st.warning(
                    f"Nenhuma Alliance válida encontrada para **{exp_used}**. "
                    "São necessários decks de pelo menos 3 casas distintas."
                )
            else:
                st.success(
                    f"🏆 Top **{len(result)}** Alliances — "
                    f"expansão **{exp_used}** | estratégia **{strat_used}**"
                )
                res_display = [c for c in [
                    "score",
                    "casa_1", "deck_1",
                    "casa_2", "deck_2",
                    "casa_3", "deck_3",
                    "pod_aerc_total", "amberControl",
                    "expectedAmber", "creatureControl", "efficiency",
                    "url_1", "url_2", "url_3",
                ] if c in result.columns]
                st.dataframe(
                    result[res_display],
                    use_container_width=True,
                    hide_index=False,
                    column_config={
                        "score":           st.column_config.NumberColumn("Score",      format="%.2f"),
                        "pod_aerc_total":  st.column_config.NumberColumn("AERC Total", format="%.2f"),
                        "amberControl":    st.column_config.NumberColumn("A.Ctrl",     format="%.2f"),
                        "expectedAmber":   st.column_config.NumberColumn("E.Amb",      format="%.2f"),
                        "creatureControl": st.column_config.NumberColumn("C.Ctrl",     format="%.2f"),
                        "efficiency":      st.column_config.NumberColumn("Effic.",     format="%.2f"),
                        "url_1": st.column_config.LinkColumn("DoK 1", display_text="🔗"),
                        "url_2": st.column_config.LinkColumn("DoK 2", display_text="🔗"),
                        "url_3": st.column_config.LinkColumn("DoK 3", display_text="🔗"),
                    },
                )
                download_row(result, f"alliances_{exp_used}_{strat_used}", "Alliances")

    # ── TAB 2: Análise por Casa ─────────────────────────────
    with tab_pods:
        st.subheader("🏠 Análise por Casa (Pod)")
        st.markdown(
            "Cada linha representa **uma casa** de um deck. "
            "As métricas AERC são somadas para todas as cartas daquela casa, "
            "permitindo comparar a contribuição de cada pod de forma isolada."
        )

        p_exp_opts = ["Todas"] + sorted(df_pods["expansionAbbr"].dropna().unique()) \
            if "expansionAbbr" in df_pods.columns else ["Todas"]
        sel_p_exp = st.selectbox("Expansão", p_exp_opts, key="pods_exp")

        df_pods_view = df_pods if sel_p_exp == "Todas" \
            else df_pods[df_pods["expansionAbbr"] == sel_p_exp]

        pod_display = [c for c in [
            "deck_name", "expansionAbbr", "house",
            "pod_aerc", "dimensional_score",
            "sum_expectedAmber", "sum_amberControl",
            "sum_creatureControl", "sum_artifactControl",
            "sum_efficiency", "sum_disruption",
            "creatures", "actions", "artifacts", "upgrades",
            "dok_url",
        ] if c in df_pods_view.columns]

        st.dataframe(
            df_pods_view[pod_display],
            use_container_width=True,
            hide_index=True,
            column_config={
                "dok_url":             st.column_config.LinkColumn("DoK", display_text="🔗"),
                "deck_name":           st.column_config.TextColumn("Deck", width="large"),
                "pod_aerc":            st.column_config.NumberColumn("AERC Pod",   format="%.2f"),
                "dimensional_score":   st.column_config.NumberColumn("Dim.Score",  format="%.2f"),
                "sum_expectedAmber":   st.column_config.NumberColumn("E.Amb",      format="%.2f"),
                "sum_amberControl":    st.column_config.NumberColumn("A.Ctrl",     format="%.2f"),
                "sum_creatureControl": st.column_config.NumberColumn("C.Ctrl",     format="%.2f"),
                "sum_efficiency":      st.column_config.NumberColumn("Effic.",     format="%.2f"),
            },
        )
        st.caption(f"{len(df_pods_view)} pod(s) exibido(s)")
        download_row(df_pods, "pods_por_casa", "Pods por Casa")

    # ── TAB 3: Resumo ───────────────────────────────────────
    with tab_resumo:
        st.subheader("📊 Visão Geral da Coleção")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total de Decks", len(df))
        if "sasRating" in df.columns:
            sas = df["sasRating"].dropna()
            c2.metric("SAS Médio",  f"{sas.mean():.1f}")
            c3.metric("SAS Máximo", int(sas.max()))
            c4.metric("SAS Mínimo", int(sas.min()))
        if "expansionAbbr" in df.columns:
            c5.metric("Expansões",  df["expansionAbbr"].nunique())

        st.markdown("#### Decks por expansão")
        if "expansionAbbr" in df.columns:
            exp_tbl = (
                df["expansionAbbr"]
                .value_counts()
                .reset_index()
                .rename(columns={"expansionAbbr": "Expansão", "count": "Decks"})
            )
            st.dataframe(exp_tbl, use_container_width=True, hide_index=True)

        st.markdown("#### Frequência de casas")
        if "houses" in df.columns:
            house_cnt: Counter = Counter()
            for h_str in df["houses"].dropna():
                for h in h_str.split(", "):
                    house_cnt[h] += 1
            house_tbl = pd.DataFrame(
                house_cnt.most_common(), columns=["Casa", "Aparições"]
            )
            st.dataframe(house_tbl, use_container_width=True, hide_index=True)

    # ── TAB 4: Meus Decks ───────────────────────────────────
    with tab_decks:
        st.subheader("🃏 Todos os Seus Decks")

        fc1, fc2 = st.columns([1, 3])
        with fc1:
            exp_opts = ["Todas"] + sorted(df["expansionAbbr"].dropna().unique()) \
                if "expansionAbbr" in df.columns else ["Todas"]
            sel_exp = st.selectbox("Expansão", exp_opts, key="decks_exp")
        with fc2:
            search = st.text_input("🔍 Buscar por nome do deck", "", key="decks_search")

        df_view = df.copy()
        if sel_exp != "Todas":
            df_view = df_view[df_view["expansionAbbr"] == sel_exp]
        if search:
            df_view = df_view[df_view["name"].str.contains(search, case=False, na=False)]

        display = [c for c in [
            "name", "expansionAbbr", "houses",
            "sasRating", "aercScore", "synergyRating", "antisynergyRating",
            "expectedAmber", "amberControl", "creatureControl", "effectivePower",
            "wins", "losses", "powerLevel", "chains",
            "dok_url",
        ] if c in df_view.columns]

        st.dataframe(
            df_view[display],
            use_container_width=True,
            hide_index=True,
            column_config={
                "dok_url":            st.column_config.LinkColumn("DoK", display_text="🔗 Abrir"),
                "name":               st.column_config.TextColumn("Deck", width="large"),
                "expansionAbbr":      st.column_config.TextColumn("Set"),
                "sasRating":          st.column_config.NumberColumn("SAS"),
                "aercScore":          st.column_config.NumberColumn("AERC"),
                "synergyRating":      st.column_config.NumberColumn("Syn"),
                "antisynergyRating":  st.column_config.NumberColumn("Anti"),
                "expectedAmber":      st.column_config.NumberColumn("E.Amb", format="%.2f"),
                "amberControl":       st.column_config.NumberColumn("A.Ctrl", format="%.2f"),
                "creatureControl":    st.column_config.NumberColumn("C.Ctrl", format="%.2f"),
                "effectivePower":     st.column_config.NumberColumn("Eff.Pwr"),
            },
        )
        st.caption(f"{len(df_view)} deck(s) exibido(s)")
        download_row(df, "meus_decks", "Meus Decks")

    # ── TAB 5: Gráficos ─────────────────────────────────────
    with tab_graficos:
        st.subheader("📈 Gráficos da Coleção")

        gc1, gc2 = st.columns(2)
        with gc1:
            if "sasRating" in df.columns:
                fig, ax = plt.subplots(figsize=(6, 4))
                df["sasRating"].dropna().hist(bins=20, ax=ax, color="steelblue", edgecolor="white")
                ax.set_title("Distribuição de SAS")
                ax.set_xlabel("SAS")
                ax.set_ylabel("Nº de decks")
                ax.grid(axis="y", linestyle="--", alpha=0.5)
                st.pyplot(fig)
                plt.close(fig)

        with gc2:
            if "expansionAbbr" in df.columns:
                fig, ax = plt.subplots(figsize=(6, 4))
                df["expansionAbbr"].value_counts().plot(kind="bar", ax=ax, color="indianred")
                ax.set_title("Decks por Expansão")
                ax.set_ylabel("Nº de decks")
                ax.tick_params(axis="x", rotation=45)
                ax.grid(axis="y", linestyle="--", alpha=0.5)
                st.pyplot(fig)
                plt.close(fig)

        if "houses" in df.columns:
            house_cnt: Counter = Counter()
            for h_str in df["houses"].dropna():
                for h in h_str.split(", "):
                    house_cnt[h] += 1
            if house_cnt:
                hdf = pd.DataFrame(house_cnt.most_common(), columns=["Casa", "Freq"])
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(hdf["Casa"], hdf["Freq"], color="mediumseagreen", edgecolor="white")
                ax.set_title("Frequência de Casas na Coleção")
                ax.set_ylabel("Aparições")
                ax.tick_params(axis="x", rotation=45)
                ax.grid(axis="y", linestyle="--", alpha=0.5)
                st.pyplot(fig)
                plt.close(fig)

        if "sasRating" in df.columns and "aercScore" in df.columns:
            st.markdown("#### SAS vs AERC")
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.scatter(
                df["aercScore"], df["sasRating"],
                alpha=0.6, color="mediumpurple", edgecolors="white", linewidths=0.5
            )
            ax.set_xlabel("AERC Score")
            ax.set_ylabel("SAS Rating")
            ax.set_title("Correlação SAS × AERC")
            ax.grid(linestyle="--", alpha=0.4)
            st.pyplot(fig)
            plt.close(fig)


def main() -> None:
    st.set_page_config(
        page_title="KeyForge Deck Analyzer",
        page_icon="🔑",
        layout="wide",
    )

    st.title("🔑 KeyForge Deck Analyzer")

    # ── Se dados já estão em memória, vai direto para os resultados ──
    if "df" in st.session_state and "df_pods" in st.session_state:
        _render_results(st.session_state["df"], st.session_state["df_pods"])
        return

    # ── Tela inicial: introdução + formulário ─────────────────────
    st.markdown("""
    ### O que é esta ferramenta?

    Esta página se conecta à API pública do [**Decks of KeyForge (DoK)**](https://decksofkeyforge.com)
    e analisa **todos os decks marcados como seus** na plataforma, gerando quatro visões:

    | | |
    |---|---|
    | 🏰 **Alliance Optimizer** | Melhores combinações de pods por expansão e estratégia (Control, Rush...) |
    | 🏠 **Análise por Casa** | Qual das 3 casas de cada deck contribui mais para o AERC total |
    | 🃏 **Meus Decks** | Lista completa com ~50 métricas por deck: SAS, AERC, casas, contagens, wins/losses... |
    | 📈 **Gráficos** | Distribuição de SAS, decks por expansão e frequência de casas |

    Ao final de cada aba você pode **baixar os dados** em CSV ou Excel para análise própria.

    ---

    ### Como usar

    1. **Gere sua API key** em [decksofkeyforge.com/about/sellers-and-devs](https://decksofkeyforge.com/about/sellers-and-devs)
       *(faça login → role até o fim → clique em "Generate API Key")*
    2. Verifique que seus decks estão marcados no DoK com **"I own this deck"**
    3. Cole a chave abaixo e clique em **Analisar meus decks**

    > 🔒 **Privacidade:** sua chave API **nunca é salva**. Ela existe apenas na memória desta sessão
    > para fazer as requisições ao DoK e desaparece ao fechar a aba.
    """)

    st.divider()

    with st.form("api_form"):
        api_key = st.text_input(
            "🔑 Cole sua API Key do Decks of KeyForge",
            type="password",
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            help="Gerada em decksofkeyforge.com/about/sellers-and-devs",
        )
        submitted = st.form_submit_button("🚀 Analisar meus decks", use_container_width=True)

    if not submitted:
        st.stop()

    # ── Validação básica ──────────────────────────────────────────
    api_key = api_key.strip()
    if not api_key:
        st.error("⚠️ Por favor insira sua API Key antes de continuar.")
        st.stop()

    headers = make_headers(api_key)

    # ── Pipeline de dados (executado UMA única vez por sessão) ────
    with st.status("⏳ Carregando seus dados...", expanded=True) as status:

        st.write("📋 Buscando lista de decks...")
        try:
            my_decks = fetch_my_decks(headers)
        except requests.exceptions.HTTPError as e:
            status.update(label="Erro", state="error")
            code = e.response.status_code
            if code == 401:
                st.error("❌ API Key inválida ou expirada. Verifique e tente novamente.")
            else:
                st.error(f"❌ Erro HTTP {code} ao acessar a API do DoK.")
            st.stop()
        st.write(f"✅ {len(my_decks)} decks encontrados")

        st.write(f"🔍 Buscando detalhes de {len(my_decks)} decks (pode levar alguns minutos)...")
        progress_bar = st.progress(0, text="Iniciando...")
        detailed_decks: list[dict] = []
        failed: list[str] = []

        for i, deck in enumerate(my_decks):
            kid = deck.get("keyforgeId") or deck.get("keyforge_id") or deck.get("id")
            if not kid:
                continue
            detail = fetch_deck_details(str(kid), headers)
            if detail is None:
                failed.append(str(kid))
            else:
                deck_obj = detail.get("deck", detail) if isinstance(detail, dict) else detail
                detailed_decks.append(deck_obj)

            pct = (i + 1) / len(my_decks)
            progress_bar.progress(pct, text=f"{i + 1}/{len(my_decks)} decks")
            time.sleep(0.25)
            if (i + 1) % 50 == 0:
                time.sleep(5.0)

        progress_bar.empty()
        msg = f"✅ {len(detailed_decks)} decks processados"
        if failed:
            msg += f" | ⚠️ {len(failed)} falharam"
        st.write(msg)

        st.write("📚 Carregando banco de cartas do DoK...")
        try:
            all_cards = fetch_all_cards(headers)
        except Exception as e:
            st.warning(f"⚠️ Não foi possível carregar o banco de cartas: {e}. A aba de Pods pode ficar incompleta.")
            all_cards = []
        st.write(f"✅ {len(all_cards)} cartas carregadas")

        st.write("⚙️ Calculando métricas...")
        df = build_decks_df(detailed_decks)
        df_pods = build_pods_df(detailed_decks, all_cards)

        # ── Salva em session_state — a partir daqui nunca mais chama a API ──
        st.session_state["df"]             = df
        st.session_state["df_pods"]        = df_pods
        st.session_state["detailed_decks"] = detailed_decks

        status.update(
            label=f"✅ Concluído! {len(df)} decks analisados.",
            state="complete",
            expanded=False,
        )

    # Rerun limpo: na próxima execução cai no bloco "dados em memória" acima
    st.rerun()


if __name__ == "__main__":
    main()
