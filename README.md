# Analyse des données NEO/NASA

## API Flask

### Installation

```
docker-compose build
docker-compose up
```

Flask écoute sur [http://0.0.0.0:5000].

### Utilisation

La page d'accueil présente la liste des caractéristiques numériques disponibles pour chaque objet.

Pour voir la distribution d'une caractéristique : `http://0.0.0.0:5000/plots/1D/<nom_caractéristique>/`.

Pour voir la distribution d'une caractéristique en fonction d'une autre : `http://0.0.0.0:5000/plots/2D/<caract1>/<caract2>/`.

Pour lancer une classification non supervisée : `http://0.0.0.0:5000/classify/<classificateur>/<option>/` (pour l'instant seul l'algorithme k-means de `scikit-learn` est implémenté, avec comme option le nombre de noyaux — 2 par défaut).

## Jupyter Notebook

### Installation

```
docker-compose -f docker-compose-jupyter.yml build
docker-compose -f docker-compose-jupyter.yml up
```

La dernière commande indique l'URL + token à utiliser.
