# 🎓 Partie Pratique — IA & Data Warehouse
## Exposé M1 Informatique — 2024/2025

---

## 📁 Structure du projet

```
projet_dw_ia/
├── docker-compose.yml          ← PostgreSQL + pgAdmin
├── requirements.txt            ← Dépendances Python
├── data/
│   ├── ventes_raw.csv          ← Généré par etl.py (données brutes)
│   ├── ventes_clean.csv        ← Après transformation ETL
│   └── resultats_ml.png        ← Graphiques du modèle IA
└── scripts/
    ├── init_dw.sql             ← Schéma en étoile PostgreSQL
    ├── etl.py                  ← Pipeline Extract-Transform-Load
    └── modele_ia.py            ← Modèle Random Forest + visualisations
```

---

## 🚀 Démarrage en 4 étapes

### Étape 1 — Lancer le Data Warehouse (Docker)
```bash
docker-compose up -d
```
- PostgreSQL tourne sur **localhost:5432**
- pgAdmin (interface web) sur **http://localhost:8080**
  - Email    : admin@dw.com
  - Password : admin123

### Étape 2 — Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### Étape 3 — Lancer le pipeline ETL
```bash
python scripts/etl.py
```
Ce script va :
1. Générer 5 000 ventes simulées → `data/ventes_raw.csv`
2. Nettoyer et enrichir les données (pandas)
3. Charger le schéma en étoile dans PostgreSQL :
   - `dim_temps`, `dim_produit`, `dim_client`, `dim_magasin`
   - `fait_ventes` (table des faits)

### Étape 4 — Entraîner et évaluer le modèle IA
```bash
python scripts/modele_ia.py
```
Ce script va :
1. Extraire les features via une requête SQL sur le DW
2. Préparer et encoder les variables
3. Entraîner un **Random Forest** (200 arbres)
4. Afficher : MAE, RMSE, R²
5. Générer 4 graphiques → `data/resultats_ml.png`

---

## 🔌 Connexion SQL Developer

Dans SQL Developer, créer une connexion :
- **Hostname** : localhost
- **Port**     : 5432
- **Database** : datawarehouse
- **Username** : dw_user
- **Password** : dw_pass123

Requêtes OLAP à montrer pendant l'exposé :
```sql
-- CA par catégorie et trimestre
SELECT p.categorie, t.trimestre, t.annee,
       SUM(f.montant_ttc) AS ca_total,
       COUNT(*) AS nb_ventes
FROM fait_ventes f
JOIN dim_produit p ON f.id_produit = p.id_produit
JOIN dim_temps   t ON f.id_temps   = t.id_temps
GROUP BY p.categorie, t.trimestre, t.annee
ORDER BY t.annee, t.trimestre;

-- Top 5 régions par CA
SELECT m.region, SUM(f.montant_ttc) AS ca
FROM fait_ventes f
JOIN dim_magasin m ON f.id_magasin = m.id_magasin
GROUP BY m.region
ORDER BY ca DESC LIMIT 5;

-- Impact des remises sur la marge
SELECT
  CASE WHEN f.remise_pct = 0 THEN 'Sans remise'
       WHEN f.remise_pct <= 10 THEN '1-10%'
       ELSE '>10%' END AS tranche_remise,
  AVG(f.marge) AS marge_moyenne,
  COUNT(*) AS nb_transactions
FROM fait_ventes f
GROUP BY 1 ORDER BY 2 DESC;
```

---

## 💡 Ce que démontre cette partie pratique

| Concept théorique         | Démonstration pratique                        |
|---------------------------|-----------------------------------------------|
| Schéma en étoile          | Tables dim_* + fait_ventes dans PostgreSQL     |
| Pipeline ETL              | etl.py : Extract → Transform → Load           |
| Qualité des données       | Nettoyage doublons, nulls, normalisation       |
| Feature engineering       | Enrichissement depuis le DW (dates, segments) |
| ML sur données DW         | Random Forest entraîné sur requête OLAP        |
| Évaluation modèle         | MAE, RMSE, R², distribution des résidus       |
| Importance des features   | Quelles colonnes DW sont utiles pour l'IA ?    |
