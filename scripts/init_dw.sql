-- ============================================================
--  INITIALISATION DU DATA WAREHOUSE  (schéma en étoile)
--  Exposé M1 — Intelligence Artificielle & Data Warehouse
-- ============================================================

-- ── Dimensions ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_temps (
    id_temps      SERIAL PRIMARY KEY,
    date_complete DATE        NOT NULL UNIQUE,
    jour          INTEGER     NOT NULL,  -- 1-31
    mois          INTEGER     NOT NULL,  -- 1-12
    trimestre     INTEGER     NOT NULL,  -- 1-4
    annee         INTEGER     NOT NULL,
    nom_mois      VARCHAR(20) NOT NULL,
    jour_semaine  VARCHAR(20) NOT NULL,
    est_weekend   BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dim_produit (
    id_produit    SERIAL PRIMARY KEY,
    nom_produit   VARCHAR(100) NOT NULL,
    categorie     VARCHAR(50)  NOT NULL,
    sous_categorie VARCHAR(50),
    prix_unitaire NUMERIC(10,2) NOT NULL,
    fournisseur   VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_client (
    id_client   SERIAL PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL,
    prenom      VARCHAR(100) NOT NULL,
    age         INTEGER,
    genre       CHAR(1),         -- M / F
    segment     VARCHAR(30),     -- Premium / Standard / Occasionnel
    ville       VARCHAR(100),
    region      VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_magasin (
    id_magasin  SERIAL PRIMARY KEY,
    nom_magasin VARCHAR(100) NOT NULL,
    ville       VARCHAR(100) NOT NULL,
    region      VARCHAR(50)  NOT NULL,
    surface_m2  INTEGER,
    type_magasin VARCHAR(30)  -- Hypermarché / Supermarché / Drive
);

-- ── Table des faits ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fait_ventes (
    id_vente      SERIAL PRIMARY KEY,
    -- Clés étrangères vers les dimensions
    id_temps      INTEGER REFERENCES dim_temps(id_temps),
    id_produit    INTEGER REFERENCES dim_produit(id_produit),
    id_client     INTEGER REFERENCES dim_client(id_client),
    id_magasin    INTEGER REFERENCES dim_magasin(id_magasin),
    -- Mesures (faits)
    quantite      INTEGER        NOT NULL,
    prix_unitaire NUMERIC(10,2)  NOT NULL,
    remise_pct    NUMERIC(5,2)   DEFAULT 0,
    montant_ht    NUMERIC(12,2)  NOT NULL,
    montant_ttc   NUMERIC(12,2)  NOT NULL,
    marge         NUMERIC(12,2),
    -- Metadata
    created_at    TIMESTAMP DEFAULT NOW()
);

-- ── Index pour les performances ──────────────────────────────
CREATE INDEX IF NOT EXISTS idx_fait_temps    ON fait_ventes(id_temps);
CREATE INDEX IF NOT EXISTS idx_fait_produit  ON fait_ventes(id_produit);
CREATE INDEX IF NOT EXISTS idx_fait_client   ON fait_ventes(id_client);
CREATE INDEX IF NOT EXISTS idx_fait_magasin  ON fait_ventes(id_magasin);

-- ── Vue analytique (exemple requête OLAP) ───────────────────
CREATE OR REPLACE VIEW vue_ventes_mensuelle AS
SELECT
    t.annee,
    t.mois,
    t.nom_mois,
    p.categorie,
    m.region,
    SUM(f.montant_ttc)  AS ca_total,
    SUM(f.quantite)     AS qte_totale,
    AVG(f.remise_pct)   AS remise_moyenne,
    COUNT(*)            AS nb_transactions
FROM fait_ventes f
JOIN dim_temps    t ON f.id_temps   = t.id_temps
JOIN dim_produit  p ON f.id_produit = p.id_produit
JOIN dim_magasin  m ON f.id_magasin = m.id_magasin
GROUP BY t.annee, t.mois, t.nom_mois, p.categorie, m.region
ORDER BY t.annee, t.mois;

-- Message de confirmation
DO $$ BEGIN
    RAISE NOTICE '✅ Schéma en étoile créé avec succès !';
    RAISE NOTICE '   Tables : dim_temps, dim_produit, dim_client, dim_magasin, fait_ventes';
    RAISE NOTICE '   Vue    : vue_ventes_mensuelle';
END $$;
