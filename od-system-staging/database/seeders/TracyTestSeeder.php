<?php

declare(strict_types=1);

namespace Database\Seeders;

use App\Enums\OrderStatus;
use App\Models\Campaign;
use App\Models\Order;
use App\Models\Product;
use App\Models\Transaction;
use App\Models\User;
use App\Models\Wallet;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class TracyTestSeeder extends Seeder
{
    public function run(): void
    {
        // ── Admin ──
        $admin = User::create([
            'name' => 'Admin Mantota',
            'email' => 'admin@mantota.test',
            'password' => bcrypt('password'),
            'role' => 'admin',
            'phone' => '+22900000000',
            'country' => 'BJ',
        ]);

        // ── Vendeur 1 (store_1) ──
        $vendor1 = User::create([
            'name' => 'Boutique Diallo',
            'slug' => 'boutique-diallo',
            'email' => 'diallo@mantota.test',
            'password' => bcrypt('password'),
            'role' => 'vendor',
            'phone' => '+22997000001',
            'country' => 'BJ',
            'shop_name' => 'Boutique Diallo',
            'shop_address' => 'Dakar, Plateau',
            'shop_type' => 'physical',
            'bot_status' => 'active',
            'bot_access_type' => 'paid',
            'whatsapp_bot_number' => '+22997000001',
            'referral_code' => 'DIALLO2026',
        ]);

        Wallet::create([
            'user_id' => $vendor1->id,
            'balance' => 150000,
            'pending_balance' => 25000,
            'escrow_balance' => 0,
            'referral_balance' => 0,
            'is_locked' => false,
        ]);

        // ── Vendeur 2 (store_2 / store_A) ──
        $vendor2 = User::create([
            'name' => 'Tech Store',
            'slug' => 'tech-store',
            'email' => 'tech@mantota.test',
            'password' => bcrypt('password'),
            'role' => 'vendor',
            'phone' => '+22997000002',
            'country' => 'BJ',
            'shop_name' => 'Tech Store',
            'shop_address' => 'Cotonou, Ganhi',
            'shop_type' => 'both',
            'bot_status' => 'active',
            'bot_access_type' => 'paid',
            'whatsapp_bot_number' => '+22997000002',
            'referral_code' => 'TECH2026',
        ]);

        Wallet::create([
            'user_id' => $vendor2->id,
            'balance' => 75000,
            'pending_balance' => 0,
            'escrow_balance' => 0,
            'referral_balance' => 5000,
            'is_locked' => false,
        ]);

        // ── Vendeur 3 (store_B pour test d'isolation T-014) ──
        $vendor3 = User::create([
            'name' => 'Pharmacie du Marché',
            'slug' => 'pharmacie-marche',
            'email' => 'pharma@mantota.test',
            'password' => bcrypt('password'),
            'role' => 'vendor',
            'phone' => '+22997000003',
            'country' => 'BJ',
            'shop_name' => 'Pharmacie du Marché',
            'shop_address' => 'Dakar, Médina',
            'shop_type' => 'physical',
            'bot_status' => 'active',
            'bot_access_type' => 'paid',
            'whatsapp_bot_number' => '+22997000003',
            'referral_code' => 'PHARMA2026',
        ]);

        Wallet::create([
            'user_id' => $vendor3->id,
            'balance' => 30000,
            'pending_balance' => 0,
            'escrow_balance' => 0,
            'referral_balance' => 0,
            'is_locked' => false,
        ]);

        // ── Influencer / Partenaire ──
        $influencer = User::create([
            'name' => 'Awa Influenceuse',
            'slug' => 'awa-influenceuse',
            'email' => 'awa@mantota.test',
            'password' => bcrypt('password'),
            'role' => 'influencer',
            'phone' => '+22997000004',
            'country' => 'BJ',
            'referral_code' => 'AWA2026',
            'tiktok_followers' => 50000,
            'instagram_followers' => 30000,
        ]);

        Wallet::create([
            'user_id' => $influencer->id,
            'balance' => 12000,
            'pending_balance' => 0,
            'escrow_balance' => 0,
            'referral_balance' => 0,
            'is_locked' => false,
        ]);

        // ── Produits du vendeur 1 ──
        $product1 = Product::create([
            'vendor_id' => $vendor1->id,
            'name' => 'Téléphone Samsung A15',
            'type' => 'physical',
            'description' => 'Samsung Galaxy A15, 128GB, 4GB RAM',
            'price' => 95000,
            'commission_percent' => 5.00,
            'stock' => 10,
            'status' => 'actif',
            'delivery_type' => 'fixed',
            'delivery_fee' => 2000,
        ]);

        $product2 = Product::create([
            'vendor_id' => $vendor1->id,
            'name' => 'Coque Samsung A15',
            'type' => 'physical',
            'description' => 'Coque transparente silicone',
            'price' => 3000,
            'commission_percent' => 10.00,
            'stock' => 50,
            'status' => 'actif',
            'delivery_type' => 'free',
            'delivery_fee' => 0,
        ]);

        $product3 = Product::create([
            'vendor_id' => $vendor1->id,
            'name' => 'Sac à main cuir',
            'type' => 'physical',
            'description' => 'Sac en cuir véritable, fait main',
            'price' => 25000,
            'commission_percent' => 8.00,
            'stock' => 5,
            'status' => 'actif',
            'delivery_type' => 'fixed',
            'delivery_fee' => 1500,
        ]);

        // ── Produits du vendeur 2 ──
        $product4 = Product::create([
            'vendor_id' => $vendor2->id,
            'name' => 'iPhone 12 Pro',
            'type' => 'physical',
            'description' => 'iPhone 12 Pro 256GB, excellent état',
            'price' => 350000,
            'commission_percent' => 5.00,
            'stock' => 3,
            'status' => 'actif',
            'delivery_type' => 'fixed',
            'delivery_fee' => 3000,
        ]);

        $product5 = Product::create([
            'vendor_id' => $vendor2->id,
            'name' => 'Écouteurs Bluetooth',
            'type' => 'physical',
            'description' => 'Écouteurs sans fil, autonomie 12h',
            'price' => 15000,
            'commission_percent' => 10.00,
            'stock' => 20,
            'status' => 'actif',
            'delivery_type' => 'free',
            'delivery_fee' => 0,
        ]);

        // ── Produits du vendeur 3 (pharmacie) ──
        $product6 = Product::create([
            'vendor_id' => $vendor3->id,
            'name' => 'Paracétamol 500mg',
            'type' => 'physical',
            'description' => 'Boîte de 20 comprimés',
            'price' => 500,
            'commission_percent' => 0,
            'stock' => 200,
            'status' => 'actif',
            'delivery_type' => 'pickup_only',
            'delivery_fee' => 0,
        ]);

        // ── Commande de test ──
        $order = Order::create([
            'vendor_id' => $vendor1->id,
            'product_id' => $product1->id,
            'influencer_id' => null,
            'customer_name' => 'Client Test',
            'customer_phone' => '+22997000099',
            'customer_whatsapp' => '+22997000099',
            'customer_email' => 'client@mantota.test',
            'amount_paid' => 97000,
            'commission_amount' => 4850,
            'vendor_earnings' => 90150,
            'delivery_fee_paid' => 2000,
            'city' => 'Dakar',
            'landmark_indication' => 'Plateau, près de la banque',
            'status' => OrderStatus::PENDING,
            'reference' => 'CMD-TEST001',
            'tracking_token' => Str::random(32),
            'payment_gateway' => 'moneroo',
            'country' => 'SN',
        ]);

        // ── Transactions de test ──
        Transaction::create([
            'user_id' => $vendor1->id,
            'type' => 'earning',
            'amount_target' => 90000,
            'gateway_fee' => 2000,
            'mantota_markup' => 3000,
            'amount_total' => 95000,
            'status' => 'completed',
            'reference' => 'TX-EARN001',
            'description' => 'Vente produit Samsung A15',
        ]);

        Transaction::create([
            'user_id' => $vendor1->id,
            'type' => 'deposit',
            'amount_target' => 50000,
            'gateway_fee' => 500,
            'mantota_markup' => 0,
            'amount_total' => 50500,
            'status' => 'completed',
            'reference' => 'TX-DEP001',
            'description' => 'Dépôt wallet',
        ]);

        // ── Campagne de test ──
        Campaign::create([
            'vendor_id' => $vendor1->id,
            'product_id' => $product1->id,
            'title' => 'Promo Samsung A15',
            'target_url' => 'https://mantota.test/product/samsung-a15',
            'total_budget' => 50000,
            'status' => 'active',
            'niche' => 'tech',
            'social_network' => 'tiktok',
            'influencer_type' => 'micro',
        ]);
    }
}
