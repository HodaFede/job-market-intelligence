"""NLP simple et explicable pour l'analyse des compétences.

1. Extraction par dictionnaire + expressions régulières (config/skills_dictionary.yaml) :
   - texte normalisé (minuscules, sans accents) ;
   - bornes de mot adaptées aux noms techniques (C#, CI/CD, scikit-learn) ;
   - gestion des faux positifs français (« tableau de bord » ≠ Tableau, « R&D » ≠ R).
2. TF-IDF par famille de métier pour faire émerger les termes caractéristiques
   absents du dictionnaire (veille : nouveaux outils, vocabulaire métier).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from jmi.clean.normalize import strip_accents

FRENCH_STOPWORDS = set("""
a ai au aux avec ce ces cet cette d dans de des du elle en et eux il ils je l la le les leur leurs lui ma mais me
meme mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos
votre vous c y ete etre avoir fait faire plus tres tout tous toute toutes ainsi afin comme dont entre sein selon sous
chez vers lors etc via n s sont est sera serez seront peut pouvez ont avez nos notre leurs ceux celle celles cela
""".split())

RECRUITMENT_STOPWORDS = set("""
poste postes profil profils mission missions equipe equipes entreprise societe groupe client clients candidat
candidate candidats recherche recherchons recrute recrutons rejoindre rejoignez offre offres h f hf cdi cdd stage
alternance experience experiences ans annee annees competences competence recherchees souhaitee souhaite requis
minimum possible jours jour semaine semaines selon politique interne travail teletravail hybride site remote full
salaire brut avantages formation diplome bac niveau junior senior confirme lead data donnees vos nos votre notre
role responsabilites principales construirez participerez accompagnerez fiabiliserez automatiserez conception mise
production projets projet metier metiers recrute un une
""".split())


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    type: str
    regex: re.Pattern


def _prepare(text: str, case_sensitive: bool) -> str:
    text = strip_accents(text.replace("’", "'"))
    return text if case_sensitive else text.lower()


class SkillExtractor:
    def __init__(self, dictionary_path: Path):
        with open(dictionary_path, encoding="utf-8") as fh:
            entries = yaml.safe_load(fh)["skills"]
        self.skills: list[Skill] = []
        for e in entries:
            cs = bool(e.get("case_sensitive"))
            patterns = [_prepare(p, cs) for p in e["patterns"]]
            body = "|".join(f"(?:{p})" for p in patterns)
            regex = re.compile(rf"(?<![\w+#])(?:{body})(?![\w+#])", 0 if cs else re.IGNORECASE)
            self.skills.append(Skill(e["name"], e["category"], e.get("type", "tech"), regex))

    def extract(self, text: str | None) -> list[str]:
        if not text:
            return []
        lower = _prepare(text, False)
        raw = _prepare(text, True)
        found = []
        for skill in self.skills:
            target = raw if not (skill.regex.flags & re.IGNORECASE) else lower
            if skill.regex.search(target):
                found.append(skill.name)
        return found

    def catalog(self) -> pd.DataFrame:
        return pd.DataFrame([{"skill": s.name, "category": s.category, "skill_type": s.type} for s in self.skills])

    def offer_skills(self, offers: pd.DataFrame) -> pd.DataFrame:
        """Table d'association offre ↔ compétence (format long, idéal pour Tableau et SQL)."""
        meta = {s.name: (s.category, s.type) for s in self.skills}
        rows = []
        for offer_id, title, desc in offers[["offer_id", "title", "description"]].itertuples(index=False):
            for name in self.extract(f"{title}\n{desc}"):
                rows.append({"offer_id": offer_id, "skill": name, "category": meta[name][0],
                             "skill_type": meta[name][1]})
        return pd.DataFrame(rows, columns=["offer_id", "skill", "category", "skill_type"])


def top_terms_by_group(offers: pd.DataFrame, group_col: str = "role_family", top_n: int = 25,
                       min_df: int = 3) -> pd.DataFrame:
    """Termes les plus caractéristiques de chaque groupe (TF-IDF moyen, uni- et bi-grammes)."""
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

    cols = ["role_family", "term", "tfidf_score", "rank"]
    docs = offers["description"].fillna("")
    if docs.str.len().sum() == 0 or len(offers) < min_df:
        return pd.DataFrame(columns=cols)
    stop = FRENCH_STOPWORDS | RECRUITMENT_STOPWORDS | set(ENGLISH_STOP_WORDS)
    token_re = re.compile(r"\b[a-z][a-z0-9+#/\-]*[a-z0-9+#]")

    def analyzer(text: str) -> list[str]:
        """Uni- et bi-grammes calculés à l'intérieur d'un même segment : une virgule ou un point
        coupe la séquence, pour ne pas créer de faux bigrammes entre deux items d'une liste."""
        grams: list[str] = []
        for segment in re.split(r"[,.;:!?()\n•|]+", strip_accents(text.lower())):
            tokens = [t for t in token_re.findall(segment) if t not in stop]
            grams.extend(tokens)
            grams.extend(f"{a} {b}" for a, b in zip(tokens, tokens[1:]))
        return grams

    vec = TfidfVectorizer(analyzer=analyzer, min_df=min_df, max_df=0.6, sublinear_tf=True)
    try:
        matrix = vec.fit_transform(docs)
    except ValueError:  # corpus trop petit ou trop homogène : aucun terme ne passe les seuils
        return pd.DataFrame(columns=cols)
    terms = vec.get_feature_names_out()
    out = []
    groups = offers[group_col].to_numpy()
    for group in sorted(set(groups)):
        mask = groups == group
        if mask.sum() < 3:
            continue
        scores = matrix[mask].mean(axis=0).A1
        ranked = [(terms[i], float(scores[i])) for i in scores.argsort()[::-1][: top_n * 3] if scores[i] > 0]
        # Un unigramme déjà porté par un bigramme presque aussi fort (« hugging » / « hugging face ») est redondant.
        bigrams = {t: s for t, s in ranked if " " in t}
        kept = [(t, s) for t, s in ranked
                if " " in t or not any(t in b.split() and bs >= 0.9 * s for b, bs in bigrams.items())]
        out.extend({"role_family": group, "term": t, "tfidf_score": round(s, 5), "rank": rank}
                   for rank, (t, s) in enumerate(kept[:top_n], start=1))
    return pd.DataFrame(out, columns=cols)
