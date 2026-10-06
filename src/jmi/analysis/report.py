"""Rapport d'insights métier généré automatiquement à partir des exports (reports/insights.md).

Les chiffres sont recalculés à chaque exécution ; les recommandations suivent des règles
simples et transparentes, à relire et compléter avec ton regard métier.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd


def _eur(x: float | None) -> str:
    return "n.d." if x is None or pd.isna(x) else f"{x:,.0f} €".replace(",", " ")


def _top(df: pd.DataFrame, label: str, value: str, n: int = 5, fmt=lambda v: f"{v}") -> str:
    rows = df.nlargest(n, value)
    return "\n".join(f"{i}. **{r[label]}** — {fmt(r[value])}" for i, (_, r) in enumerate(rows.iterrows(), 1))


def build_report(exports_dir: Path, out_path: Path) -> str:
    read = lambda name: pd.read_csv(exports_dir / f"{name}.csv")  # noqa: E731
    kpi = read("kpi_globaux").iloc[0]
    skills = read("competences_par_metier")
    salaries = read("salaires_metier_seniorite")
    cities = read("villes")
    sectors = read("secteurs")
    remote = read("teletravail_metier")
    premium = read("prime_salariale_competences")
    pairs = read("paires_competences")
    seniority = read("seniorite_metier")

    is_demo = str(kpi["jeu_de_donnees"]).startswith("Démo")
    all_roles = skills[skills["metier"] == "Tous métiers"]
    tech = all_roles[all_roles["type_competence"] == "Technologie"]
    soft = all_roles[all_roles["categorie_competence"] == "Soft skills"]
    methods = all_roles[(all_roles["type_competence"] != "Technologie")
                        & (all_roles["categorie_competence"] != "Soft skills")]
    offers = read("offres")
    links = read("offres_competences")

    def role_skills(role: str, n: int = 6) -> str:
        sub = skills[(skills["metier"] == role) & (skills["type_competence"] == "Technologie")].nlargest(n, "nb_offres")
        return ", ".join(f"{r.competence} ({r.part_offres_pct:.0f} %)" for r in sub.itertuples()) or "n.d."

    roles_by_volume = skills[skills["metier"] != "Tous métiers"].groupby("metier")["nb_offres_metier"].max() \
        .sort_values(ascending=False)
    weighted = salaries.assign(w=salaries["salaire_median"] * salaries["nb_offres_avec_salaire"])
    grouped = weighted.groupby("metier")[["w", "nb_offres_avec_salaire"]].sum()
    sal_role = (grouped["w"] / grouped["nb_offres_avec_salaire"]).sort_values(ascending=False)
    junior_share = seniority[seniority["seniorite"].isin(["Junior", "Stage / Alternance"])] \
        .groupby("metier")["part_offres_pct"].sum().sort_values(ascending=False)
    remote_share = remote[remote["teletravail"].isin(["Hybride", "Full remote"])] \
        .groupby("metier")["part_offres_pct"].sum().sort_values(ascending=False)
    cities_known = cities[cities["ville"] != "Non précisé"]
    idf_share = cities.loc[cities["region"] == "Île-de-France", "nb_offres"].sum() / cities["nb_offres"].sum() * 100

    def share_any(skill_names: set[str], role: str | None = None) -> float:
        ids = offers["id_offre"] if role is None else offers.loc[offers["metier"] == role, "id_offre"]
        hit = links.loc[links["competence"].isin(skill_names), "id_offre"]
        return 100 * ids.isin(hit).mean() if len(ids) else 0.0

    cloud, genai = {"AWS", "Azure", "GCP"}, {"LLM", "IA générative", "RAG", "LangChain", "Hugging Face"}
    idf = offers["region"] == "Île-de-France"
    med_idf = offers.loc[idf, "salaire_annuel"].median()
    med_other = offers.loc[~idf & (offers["region"] != "Non précisé"), "salaire_annuel"].median()
    remote_other = 100 * offers.loc[~idf, "teletravail_possible"].mean()
    top_soft = ", ".join(soft.nlargest(2, "nb_offres")["competence"]).lower()

    bi = all_roles.set_index("competence")["part_offres_pct"]
    tableau_pct, pbi_pct = bi.get("Tableau", 0.0), bi.get("Power BI", 0.0)

    lines = [
        "# Insights — marché de l'emploi Data / IA",
        "",
        f"_Généré automatiquement le {date.today():%d/%m/%Y} par `python -m jmi run`._",
        "",
    ]
    if is_demo:
        lines += ["> ⚠️ **Jeu de démonstration synthétique.** Ces chiffres illustrent la méthode, pas le marché réel. "
                  "Lance la collecte réelle (`python -m jmi collect`) puis `python -m jmi run` pour les remplacer.", ""]
    lines += [
        "## 1. Vue d'ensemble",
        "",
        f"- **{int(kpi['nb_offres'])} offres** uniques, **{int(kpi['nb_entreprises'])} entreprises**, "
        f"**{int(kpi['nb_villes'])} villes**, du {kpi['date_min']} au {kpi['date_max']}.",
        f"- Salaire annuel brut **médian {_eur(kpi['salaire_median'])}** (moyen {_eur(kpi['salaire_moyen'])}), "
        f"calculé sur les {kpi['pct_offres_avec_salaire']:.0f} % d'offres qui affichent un salaire.",
        f"- **{kpi['pct_teletravail']:.0f} %** des offres mentionnent du télétravail, "
        f"**{kpi['pct_cdi']:.0f} %** sont des CDI, **{kpi['pct_offres_junior']:.0f} %** visent un profil junior ou stage/alternance.",
        f"- L'Île-de-France concentre **{idf_share:.0f} %** des offres.",
        "",
        "## 2. Métiers",
        "",
        "Volume d'offres par métier :",
        "",
        *[f"- {role} : {int(n)} offres" for role, n in roles_by_volume.items()],
        "",
        "Salaire médian (pondéré par séniorité) :",
        "",
        *[f"- {role} : {_eur(v)}" for role, v in sal_role.items()],
        "",
        "## 3. Compétences et technologies",
        "",
        "Technologies les plus demandées (tous métiers, % des offres) :",
        "",
        _top(tech, "competence", "part_offres_pct", 10, lambda v: f"{v:.0f} %"),
        "",
        "Méthodes et domaines les plus cités :",
        "",
        _top(methods, "competence", "part_offres_pct", 5, lambda v: f"{v:.0f} %"),
        "",
        "Soft skills les plus citées :",
        "",
        _top(soft, "competence", "part_offres_pct", 5, lambda v: f"{v:.0f} %"),
        "",
        "Stack type par métier :",
        "",
        *[f"- **{role}** : {role_skills(role)}" for role in roles_by_volume.index[:6]],
        "",
    ]
    if not premium.empty:
        lines += ["Compétences associées aux salaires médians les plus élevés (corrélation, pas causalité) :", "",
                  _top(premium, "competence", "prime_eur", 5,
                       lambda v: f"+{_eur(v)} vs offres sans cette compétence"), ""]
    if not pairs.empty:
        strong = pairs[pairs["nb_offres_communes"] >= 15].nlargest(5, "lift")
        lines += ["Associations de compétences les plus fortes (lift) :", "",
                  *[f"- {r.competence_a} + {r.competence_b} : lift {r.lift:.1f} ({int(r.nb_offres_communes)} offres)"
                    for r in strong.itertuples()], ""]
    lines += [
        "## 4. Géographie, secteurs, télétravail",
        "",
        "Villes qui recrutent le plus :",
        "",
        _top(cities_known, "ville", "nb_offres", 5, lambda v: f"{int(v)} offres"),
        "",
        "Secteurs qui recrutent le plus :",
        "",
        _top(sectors, "secteur", "nb_offres", 5, lambda v: f"{int(v)} offres"),
        "",
        "Métiers les plus ouverts au télétravail : " +
        ", ".join(f"{m} ({v:.0f} %)" for m, v in remote_share.head(3).items()) + ".",
        "",
        "## 5. Recommandations",
        "",
        "**Pour un candidat Data Analyst / Data Scientist junior**",
        "",
        f"- Prioriser le socle {', '.join(tech.nlargest(3, 'nb_offres')['competence'])} : il apparaît dans la "
        "majorité des offres, quel que soit le métier.",
        f"- Outils de BI : Power BI est cité dans {pbi_pct:.0f} % des offres et Tableau dans {tableau_pct:.0f} %. "
        "Maîtriser l'un et savoir transposer vers l'autre (mêmes concepts : modèle, mesures, filtres, storytelling) "
        "élargit le champ des candidatures.",
        f"- Cibler en priorité les métiers où la part d'offres junior est la plus forte : "
        + ", ".join(f"{m} ({v:.0f} %)" for m, v in junior_share.head(3).items()) + ".",
        f"- Mettre en avant {top_soft} dans le CV et les entretiens : ce sont les soft skills les plus citées.",
        "",
        "**Pour un recruteur ou un manager data**",
        "",
        f"- Seules {kpi['pct_offres_avec_salaire']:.0f} % des offres affichent un salaire : publier une fourchette "
        "est un levier de différenciation.",
        f"- Salaire médian Île-de-France {_eur(med_idf)} contre {_eur(med_other)} en régions, où "
        f"{remote_other:.0f} % des offres proposent du télétravail : recruter en régions avec télétravail élargit "
        "le vivier à coût salarial moindre.",
        "",
        "**Pour un organisme de formation**",
        "",
        f"- Un cloud (AWS / Azure / GCP) est demandé dans {share_any(cloud):.0f} % des offres "
        f"({share_any(cloud, 'Data Engineer'):.0f} % pour les Data Engineers) et l'IA générative dans "
        f"{share_any(genai, 'Data Scientist'):.0f} % des offres de Data Scientist : deux briques à intégrer aux parcours data.",
        "",
        "## 6. Limites",
        "",
        "- Salaires : uniquement les offres qui les affichent (biais possible vers certains secteurs et le secteur public).",
        "- Extraction de compétences par dictionnaire : précise et explicable, mais ne détecte que ce qui est listé "
        "(le TF-IDF sert à repérer les oublis).",
        "- Déduplication sur intitulé + entreprise + ville : deux offres réellement distinctes et identiques sur ces "
        "trois champs sont fusionnées.",
    ]
    text = "\n".join(lines) + "\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return text
