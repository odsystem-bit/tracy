# Guide d'Envoi sur GitHub - TRACY IA

## 📋 Prérequis

Git doit être installé sur votre machine. Pour l'installer:

```bash
sudo apt update
sudo apt install git
```

Configurer Git avec vos informations:

```bash
git config --global user.name "Votre Nom"
git config --global user.email "votre.email@example.com"
```

---

## 🚀 Étape 1: Initialisation du Repository

Ouvrez un terminal dans le dossier `/home/yanou/Bureau/Projet/TRACY IA` et exécutez:

```bash
cd "/home/yanou/Bureau/Projet/TRACY IA"
git init
```

---

## 📦 Étape 2: Ajouter tous les fichiers

```bash
git add .
```

Cela va ajouter:
- Tracy Core
- Backend Laravel
- Mobile App Flutter
- Admin Panel React
- Documentation (README.md, DELIVERY_REVOLUTIONARY.md, etc.)
- Fichiers de configuration

---

## ✍️ Étape 3: Premier Commit

```bash
git commit -m "Initial commit - TRACY IA Project

- Tracy Core (IA Orchestrateur) - 9 agents, 28 tools, 140+ tests
- Backend Laravel (od-system-staging) - 114 migrations, API complète
- Mobile App Flutter (mantota_app) - 30+ screens
- Admin Panel React - 20+ pages
- Documentation complète (README, système livraison, audit)

Generated with [Devin](https://devin.ai)

Co-Authored-By: Devin <158243242+devin-ai-integration[bot]@users.noreply.github.com>"
```

---

## 🔗 Étape 4: Ajouter le Remote GitHub

```bash
git remote add origin https://github.com/odsystem-bit/tracy.git
```

---

## 📤 Étape 5: Envoyer sur GitHub

```bash
git branch -M main
git push -u origin main
```

Si Git demande vos identifiants GitHub:
- Username: votre username GitHub
- Password: votre Personal Access Token (pas votre mot de passe normal)

### Pour créer un Personal Access Token:
1. Allez sur https://github.com/settings/tokens
2. Cliquez "Generate new token" → "Generate new token (classic)"
3. Cochez "repo" (full control of private repositories)
4. Cliquez "Generate token"
5. Copiez le token (il ne sera plus affiché !)
6. Utilisez ce token comme mot de passe

---

## ✅ Vérification

Une fois envoyé, allez sur:
https://github.com/odsystem-bit/tracy

Vous devriez voir:
- Tous les fichiers du projet
- Le README.md comme page d'accueil
- L'historique des commits

---

## 🔄 Mises à jour futures

Pour envoyer des modifications futures:

```bash
git add .
git commit -m "Description des modifications"
git push
```

---

## 📚 Structure sur GitHub

Le repository aura cette structure:

```
tracy/
├── README.md                          # Page d'accueil du projet
├── DELIVERY_REVOLUTIONARY.md          # Système de livraison détaillé
├── LAUNCH_READINESS.md                # Points critiques lancement
├── AUDIT_REPORT.md                    # Audit complet
├── DEV_PLAN.md                       # Plan de développement
├── ADMIN_SPEC.md                     # Spécification Admin Panel
├── TRACY_TRAINING_PLAN.md            # Plan d'entraînement Tracy
├── META_WHATSAPP_TROUBLESHOOTING.md  # Guide résolution WhatsApp
├── tracy-core/                       # Orchestrateur IA
├── od-system-staging/                # Backend Laravel
├── mantota_app/                      # Mobile App Flutter
├── admin-panel/                      # Admin Panel React
├── docs/                            # Documentation
└── whatsapp-bot-legacy/              # Legacy (non utilisé)
```

---

## 🎯 Prochaine étape après l'envoi

Une fois sur GitHub:
1. Activer GitHub Actions (pour CI/CD)
2. Configurer GitHub Pages (pour la documentation)
3. Ajouter des collaborateurs si nécessaire
4. Créer des Issues pour le suivi des tâches
5. Créer des Projects pour l'organisation

---

## 💡 Astuces

### Ignorer des fichiers
Les fichiers suivants sont déjà ignorés par `.gitignore`:
- `.env` (fichiers de configuration avec secrets)
- `node_modules/` (dépendances)
- `__pycache__/` (cache Python)
- `*.sql` (fichiers de base de données)
- Fichiers temporaires

### Vérifier le statut
```bash
git status
```

### Voir l'historique
```bash
git log
```

### Annuler un commit (si erreur)
```bash
git reset --soft HEAD~1
```

---

## 🆘 Problèmes courants

### Erreur: "remote origin already exists"
```bash
git remote set-url origin https://github.com/odsystem-bit/tracy.git
```

### Erreur: "Authentication failed"
- Vérifiez que vous utilisez un Personal Access Token
- Vérifiez que le token a les permissions "repo"

### Erreur: "Permission denied"
- Vérifiez que vous avez les droits sur le repository
- Contactez le propriétaire du repository

---

## 📞 Support

Si vous rencontrez des problèmes:
- Documentation Git: https://git-scm.com/doc
- Documentation GitHub: https://docs.github.com
