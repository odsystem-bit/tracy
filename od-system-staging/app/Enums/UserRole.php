<?php

declare(strict_types=1);

namespace App\Enums;

/**
 * UserRole — Rôles utilisateur de la plateforme.
 *
 *  - BUYER       : Acheteur qui discute avec Tracy, découvre des produits et commande.
 *  - VENDOR      : Vendeur qui crée et gère sa boutique, son catalogue et ses commandes.
 *  - INFLUENCER  : Créateur de contenu qui diffuse les liens et perçoit les revenus.
 *  - ADMIN       : Administrateur plateforme avec accès complet.
 */
enum UserRole: string
{
    case BUYER      = 'buyer';
    case VENDOR     = 'vendor';
    case INFLUENCER = 'influencer';
    case ADMIN      = 'admin';
}
