#!/bin/bash

# Script pour envoyer le projet TRACY IA sur GitHub
# À exécuter dans le dossier TRACY IA

set -e  # Arrête si une erreur survient

echo "🚀 Configuration de Git pour TRACY IA..."
echo ""

# Vérifier si git est installé
if ! command -v git &> /dev/null; then
    echo "❌ Git n'est pas installé. Installez-le d'abord:"
    echo "   sudo apt update && sudo apt install git"
    exit 1
fi

# Configurer git (si pas déjà configuré)
echo "📝 Configuration Git..."
read -p "Votre nom GitHub: " git_name
read -p "Votre email GitHub: " git_email

git config --global user.name "$git_name"
git config --global user.email "$git_email"

echo "✅ Git configuré avec: $git_name <$git_email>"
echo ""

# Créer le repository principal
echo "📦 Initialisation repository principal..."
git init
git add .
git commit -m "Initial commit - TRACY IA Project

- Tracy Core (IA Orchestrateur)
- Backend Laravel (od-system-staging)
- Mobile App Flutter (mantota_app)
- Admin Panel React
- Documentation complète

Generated with [Devin](https://devin.ai)

Co-Authored-By: Devin <158243242+devin-ai-integration[bot]@users.noreply.github.com>"

echo "✅ Repository principal initialisé"
echo ""

# Ajouter le remote
echo "🔗 Ajout du remote GitHub..."
git remote add origin https://github.com/odsystem-bit/tracy.git
echo "✅ Remote ajouté: https://github.com/odsystem-bit/tracy.git"
echo ""

# Push vers GitHub
echo "📤 Envoi vers GitHub..."
git branch -M main
git push -u origin main

echo "✅ Projet envoyé sur GitHub !"
echo ""
echo "🎉 Succès ! Le projet est maintenant sur:"
echo "   https://github.com/odsystem-bit/tracy"
echo ""
echo "📚 Documentation expliquant le système de livraison:"
echo "   - README.md (vue d'ensemble)"
echo "   - DELIVERY_REVOLUTIONARY.md (système de livraison détaillé)"
echo "   - LAUNCH_READINESS.md (points critiques)"
echo "   - AUDIT_REPORT.md (audit complet)"
