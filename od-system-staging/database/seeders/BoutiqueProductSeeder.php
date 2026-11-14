<?php

declare(strict_types=1);

namespace Database\Seeders;

use App\Models\MenuCategory;
use App\Models\MenuItem;
use App\Models\Product;
use App\Models\RestaurantHour;
use App\Models\User;
use App\Models\Wallet;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class BoutiqueProductSeeder extends Seeder
{
    public function run(): void
    {
        $vendorsData = [
            [
                'name' => 'Boutique Diallo',
                'email' => 'diallo@mantota.test',
                'shop_type' => 'physical',
                'address' => 'Dakar, Plateau',
                'lat' => 14.7167,
                'lng' => -17.4677,
                'niches' => ['telephone', 'telephonie', 'accessoires'],
            ],
            [
                'name' => 'Tech Store',
                'email' => 'tech@mantota.test',
                'shop_type' => 'both',
                'address' => 'Cotonou, Ganhi',
                'lat' => 6.3650,
                'lng' => 2.4183,
                'niches' => ['telephone', 'telephonie', 'electronique'],
            ],
            [
                'name' => 'Pharmacie du Marché',
                'email' => 'pharma@mantota.test',
                'shop_type' => 'physical',
                'address' => 'Dakar, Médina',
                'lat' => 14.6867,
                'lng' => -17.4481,
                'niches' => ['sante', 'pharmacie'],
            ],
            ['name' => 'Mode Élégance', 'email' => 'modeelegance@mantota.test', 'shop_type' => 'physical', 'address' => 'Abidjan, Plateau', 'lat' => 5.3000, 'lng' => -4.0167, 'niches' => ['mode', 'vetement']],
            ['name' => 'Fitness Pro', 'email' => 'fitnesspro@mantota.test', 'shop_type' => 'physical', 'address' => 'Cotonou, Fidjrossè', 'lat' => 6.3500, 'lng' => 2.4000, 'niches' => ['sport', 'fitness']],
            ['name' => 'Maison & Déco', 'email' => 'maisondeco@mantota.test', 'shop_type' => 'physical', 'address' => 'Porto-Novo, Centre', 'lat' => 6.4969, 'lng' => 2.6289, 'niches' => ['maison', 'deco']],
            ['name' => 'Supermarché Diallo', 'email' => 'supermarche@mantota.test', 'shop_type' => 'physical', 'address' => 'Dakar, Grand-Yoff', 'lat' => 14.7228, 'lng' => -17.4799, 'niches' => ['alimentaire', 'epicerie']],
            ['name' => 'Boulangerie Douceur', 'email' => 'boulangerie@mantota.test', 'shop_type' => 'physical', 'address' => 'Cotonou, Akpakpa', 'lat' => 6.3700, 'lng' => 2.4300, 'niches' => ['alimentaire', 'boulangerie']],
            ['name' => 'Restaurant Le Mandingue', 'email' => 'mandingu@mantota.test', 'shop_type' => 'restaurant_physical', 'address' => 'Abidjan, Cocody', 'lat' => 5.3567, 'lng' => -3.9878, 'niches' => ['restaurant', 'cuisine']],
            ['name' => 'Restaurant Chez Kadi', 'email' => 'chezkadi@mantota.test', 'shop_type' => 'restaurant_online', 'address' => 'Cotonou, Sainte Rita', 'lat' => 6.3580, 'lng' => 2.4200, 'niches' => ['restaurant', 'cuisine']],
            ['name' => 'Électro City', 'email' => 'electrocity@mantota.test', 'shop_type' => 'both', 'address' => 'Lomé, Tokoin', 'lat' => 6.1374, 'lng' => 1.2124, 'niches' => ['electromenager', 'electronique']],
            ['name' => 'Bijoux Awa', 'email' => 'bijouxawa@mantota.test', 'shop_type' => 'physical', 'address' => 'Dakar, Ngor', 'lat' => 14.7478, 'lng' => -17.5176, 'niches' => ['bijoux', 'accessoires']],
            ['name' => 'Chaussures Plus', 'email' => 'chaussuresplus@mantota.test', 'shop_type' => 'physical', 'address' => 'Abidjan, Treichville', 'lat' => 5.2867, 'lng' => -4.0017, 'niches' => ['chaussures', 'mode']],
            ['name' => 'Librairie Savoir', 'email' => 'librairie@mantota.test', 'shop_type' => 'physical', 'address' => 'Cotonou, Cadjèhoun', 'lat' => 6.3400, 'lng' => 2.4100, 'niches' => ['librairie', 'papeterie']],
            ['name' => 'Beauté Africaine', 'email' => 'beaute@mantota.test', 'shop_type' => 'physical', 'address' => 'Lomé, Adawlato', 'lat' => 6.1500, 'lng' => 1.2300, 'niches' => ['beaute', 'cosmetique']],
            ['name' => 'Jouets & Enfants', 'email' => 'jouets@mantota.test', 'shop_type' => 'physical', 'address' => 'Dakar, Liberté 6', 'lat' => 14.7312, 'lng' => -17.4550, 'niches' => ['jouets', 'enfants']],
            ['name' => 'Informatique 2000', 'email' => 'info2000@mantota.test', 'shop_type' => 'digital', 'address' => 'Cotonou, Guézo', 'lat' => 6.3550, 'lng' => 2.3900, 'niches' => ['informatique', 'ordinateur']],
            ['name' => 'Mobilier Moderne', 'email' => 'mobilier@mantota.test', 'shop_type' => 'physical', 'address' => 'Abidjan, Marcory', 'lat' => 5.3033, 'lng' => -3.9750, 'niches' => ['mobilier', 'meubles']],
            ['name' => 'Jeux Vidéo Store', 'email' => 'jeuxvideo@mantota.test', 'shop_type' => 'physical', 'address' => 'Lomé, Dékon', 'lat' => 6.1300, 'lng' => 1.2000, 'niches' => ['jeux video', 'console']],
            ['name' => 'Art & Artisanat', 'email' => 'artisanat@mantota.test', 'shop_type' => 'physical', 'address' => 'Dakar, Soumbédioune', 'lat' => 14.7130, 'lng' => -17.4780, 'niches' => ['art', 'artisanat']],
        ];

        $vendors = [];
        foreach ($vendorsData as $index => $data) {
            $vendor = User::updateOrCreate(
                ['email' => $data['email']],
                [
                    'name' => $data['name'],
                    'slug' => Str::slug($data['name']),
                    'password' => bcrypt('password'),
                    'role' => 'vendor',
                    'phone' => '+229' . str_pad((string) (97000000 + $index + 1), 8, '0', STR_PAD_LEFT),
                    'country' => in_array($data['address'], ['Dakar, Plateau', 'Dakar, Médina', 'Dakar, Grand-Yoff', 'Dakar, Ngor', 'Dakar, Liberté 6', 'Dakar, Soumbédioune']) ? 'SN' : (str_contains($data['address'], 'Abidjan') ? 'CI' : (str_contains($data['address'], 'Lomé') ? 'TG' : 'BJ')),
                    'shop_name' => $data['name'],
                    'shop_address' => $data['address'],
                    'shop_type' => $data['shop_type'],
                    'shop_latitude' => $data['lat'],
                    'shop_longitude' => $data['lng'],
                    'niches' => $data['niches'] ?? [],
                    'bot_status' => 'active',
                    'bot_access_type' => 'paid',
                    'whatsapp_bot_number' => '+229' . str_pad((string) (97000000 + $index + 1), 8, '0', STR_PAD_LEFT),
                    'referral_code' => 'MANTO' . str_pad((string) ($index + 1), 4, '0', STR_PAD_LEFT),
                    'kyc_status' => 'approved',
                    'email_verified_at' => now(),
                ]
            );

            Wallet::firstOrCreate(
                ['user_id' => $vendor->id],
                [
                    'balance' => random_int(10000, 200000),
                    'pending_balance' => 0,
                    'escrow_balance' => 0,
                    'referral_balance' => 0,
                    'is_locked' => false,
                ]
            );

            $vendors[$data['name']] = $vendor;
        }

        $productsData = [
            ['vendor' => 'Boutique Diallo', 'name' => 'Téléphone Samsung A15', 'price' => 95000, 'stock' => 12, 'delivery' => 'fixed', 'desc' => 'Samsung Galaxy A15, 128 Go, 4 Go RAM, écran 6.5"'],
            ['vendor' => 'Boutique Diallo', 'name' => 'Coque Samsung A15', 'price' => 3000, 'stock' => 60, 'delivery' => 'free', 'desc' => 'Coque transparente en silicone anti-choc'],
            ['vendor' => 'Boutique Diallo', 'name' => 'Chargeur USB-C 25W', 'price' => 4500, 'stock' => 35, 'delivery' => 'fixed', 'desc' => 'Chargeur rapide avec câble USB-C'],
            ['vendor' => 'Boutique Diallo', 'name' => 'Verre trempé Samsung A15', 'price' => 1500, 'stock' => 100, 'delivery' => 'free', 'desc' => 'Protection d\'écran en verre trempé'],
            ['vendor' => 'Tech Store', 'name' => 'iPhone 12 Pro', 'price' => 350000, 'stock' => 5, 'delivery' => 'fixed', 'desc' => 'iPhone 12 Pro 256 Go, excellent état'],
            ['vendor' => 'Tech Store', 'name' => 'Écouteurs Bluetooth', 'price' => 15000, 'stock' => 25, 'delivery' => 'free', 'desc' => 'Écouteurs sans fil, autonomie 12h, basses puissantes'],
            ['vendor' => 'Tech Store', 'name' => 'Xiaomi Redmi Note 12', 'price' => 120000, 'stock' => 8, 'delivery' => 'fixed', 'desc' => 'Redmi Note 12 128 Go, 6 Go RAM'],
            ['vendor' => 'Tech Store', 'name' => 'Powerbank 20000mAh', 'price' => 18000, 'stock' => 18, 'delivery' => 'fixed', 'desc' => 'Batterie externe 2 ports USB, LED'],
            ['vendor' => 'Tech Store', 'name' => 'Tecno Spark 10 Pro', 'price' => 85000, 'stock' => 10, 'delivery' => 'fixed', 'desc' => 'Tecno Spark 10 Pro, 128 Go, 8 Go RAM'],
            ['vendor' => 'Tech Store', 'name' => 'Câble USB-C 2m', 'price' => 2500, 'stock' => 80, 'delivery' => 'free', 'desc' => 'Câble nylon tressé, charge rapide'],
            ['vendor' => 'Électro City', 'name' => 'Télévision 32 pouces', 'price' => 145000, 'stock' => 6, 'delivery' => 'fixed', 'desc' => 'TV LED 32" HD, 2 HDMI, USB'],
            ['vendor' => 'Électro City', 'name' => 'Réfrigérateur 150L', 'price' => 210000, 'stock' => 3, 'delivery' => 'fixed', 'desc' => 'Réfrigérateur combiné économique'],
            ['vendor' => 'Électro City', 'name' => 'Ventilateur sur pied', 'price' => 22000, 'stock' => 15, 'delivery' => 'fixed', 'desc' => 'Ventilateur 3 vitesses, hauteur réglable'],
            ['vendor' => 'Électro City', 'name' => 'Fer à repasser', 'price' => 12000, 'stock' => 20, 'delivery' => 'fixed', 'desc' => 'Fer à vapeur, semelle céramique'],
            ['vendor' => 'Électro City', 'name' => 'Micro-ondes 20L', 'price' => 65000, 'stock' => 7, 'delivery' => 'fixed', 'desc' => 'Four micro-ondes digital 700W'],
            ['vendor' => 'Informatique 2000', 'name' => 'Ordinateur portable HP', 'price' => 320000, 'stock' => 4, 'delivery' => 'fixed', 'desc' => 'HP 15s, i3, 8 Go RAM, 256 Go SSD'],
            ['vendor' => 'Informatique 2000', 'name' => 'Souris sans fil', 'price' => 8000, 'stock' => 50, 'delivery' => 'free', 'desc' => 'Souris optique sans fil USB'],
            ['vendor' => 'Informatique 2000', 'name' => 'Clavier mécanique', 'price' => 25000, 'stock' => 12, 'delivery' => 'fixed', 'desc' => 'Clavier gaming switches rouges'],
            ['vendor' => 'Informatique 2000', 'name' => 'Webcam HD', 'price' => 18000, 'stock' => 22, 'delivery' => 'fixed', 'desc' => 'Caméra 1080p avec micro intégré'],
            ['vendor' => 'Mode Élégance', 'name' => 'Robe longue wax', 'price' => 18000, 'stock' => 12, 'delivery' => 'fixed', 'desc' => 'Robe en wax africain, taille ajustable'],
            ['vendor' => 'Mode Élégance', 'name' => 'Chemise homme coton', 'price' => 12000, 'stock' => 25, 'delivery' => 'fixed', 'desc' => 'Chemise légère 100% coton'],
            ['vendor' => 'Mode Élégance', 'name' => 'Pantalon jeans', 'price' => 15000, 'stock' => 30, 'delivery' => 'fixed', 'desc' => 'Jean slim fit, plusieurs tailles'],
            ['vendor' => 'Mode Élégance', 'name' => 'T-shirt imprimé', 'price' => 7000, 'stock' => 60, 'delivery' => 'free', 'desc' => 'T-shirt coton avec motif local'],
            ['vendor' => 'Mode Élégance', 'name' => 'Boubou homme', 'price' => 25000, 'stock' => 10, 'delivery' => 'fixed', 'desc' => 'Boubou traditionnel brodé'],
            ['vendor' => 'Chaussures Plus', 'name' => 'Baskets running', 'price' => 28000, 'stock' => 20, 'delivery' => 'fixed', 'desc' => 'Baskets légères, semelle confort'],
            ['vendor' => 'Chaussures Plus', 'name' => 'Sandales cuir', 'price' => 15000, 'stock' => 35, 'delivery' => 'fixed', 'desc' => 'Sandales en cuir véritable'],
            ['vendor' => 'Chaussures Plus', 'name' => 'Mocassins homme', 'price' => 22000, 'stock' => 18, 'delivery' => 'fixed', 'desc' => 'Mocassins élégants noir et marron'],
            ['vendor' => 'Chaussures Plus', 'name' => 'Bottines femme', 'price' => 35000, 'stock' => 9, 'delivery' => 'fixed', 'desc' => 'Bottines à talon confort'],
            ['vendor' => 'Bijoux Awa', 'name' => 'Collier perles', 'price' => 12000, 'stock' => 15, 'delivery' => 'free', 'desc' => 'Collier en perles africaines'],
            ['vendor' => 'Bijoux Awa', 'name' => 'Bracelet or 18k', 'price' => 85000, 'stock' => 5, 'delivery' => 'fixed', 'desc' => 'Bracelet fin plaqué or'],
            ['vendor' => 'Bijoux Awa', 'name' => 'Boucles d\'oreilles', 'price' => 7000, 'stock' => 25, 'delivery' => 'free', 'desc' => 'Boucles en argent artisanal'],
            ['vendor' => 'Maison & Déco', 'name' => 'Lampe design', 'price' => 25000, 'stock' => 8, 'delivery' => 'fixed', 'desc' => 'Lampe sur pied design moderne'],
            ['vendor' => 'Maison & Déco', 'name' => 'Coussin motif wax', 'price' => 6000, 'stock' => 40, 'delivery' => 'free', 'desc' => 'Coussin décoratif 40x40 cm'],
            ['vendor' => 'Maison & Déco', 'name' => 'Table basse', 'price' => 75000, 'stock' => 4, 'delivery' => 'fixed', 'desc' => 'Table basse en bois massif'],
            ['vendor' => 'Mobilier Moderne', 'name' => 'Canapé 3 places', 'price' => 250000, 'stock' => 2, 'delivery' => 'fixed', 'desc' => 'Canapé tissu gris 3 places'],
            ['vendor' => 'Mobilier Moderne', 'name' => 'Chaise bureau', 'price' => 45000, 'stock' => 10, 'delivery' => 'fixed', 'desc' => 'Chaise ergonomique avec accoudoirs'],
            ['vendor' => 'Mobilier Moderne', 'name' => 'Lit 2 places', 'price' => 180000, 'stock' => 3, 'delivery' => 'fixed', 'desc' => 'Lit adulte avec sommier'],
            ['vendor' => 'Supermarché Diallo', 'name' => 'Riz 5kg', 'price' => 8500, 'stock' => 100, 'delivery' => 'fixed', 'desc' => 'Riz blanc long grain 5 kg'],
            ['vendor' => 'Supermarché Diallo', 'name' => 'Huile végétale 1L', 'price' => 1500, 'stock' => 80, 'delivery' => 'free', 'desc' => 'Huile de tournesol 1 litre'],
            ['vendor' => 'Supermarché Diallo', 'name' => 'Pâte de tomate', 'price' => 800, 'stock' => 120, 'delivery' => 'free', 'desc' => 'Concentré de tomate 400g'],
            ['vendor' => 'Supermarché Diallo', 'name' => 'Eau minérale pack', 'price' => 2500, 'stock' => 60, 'delivery' => 'fixed', 'desc' => 'Pack 6 bouteilles 1.5L'],
            ['vendor' => 'Fitness Pro', 'name' => 'Haltères 5kg', 'price' => 12000, 'stock' => 25, 'delivery' => 'fixed', 'desc' => 'Paire d\'haltères 5 kg'],
            ['vendor' => 'Fitness Pro', 'name' => 'Tapis de yoga', 'price' => 18000, 'stock' => 20, 'delivery' => 'fixed', 'desc' => 'Tapis antidérapant 6mm'],
            ['vendor' => 'Fitness Pro', 'name' => 'Corde à sauter', 'price' => 4500, 'stock' => 45, 'delivery' => 'free', 'desc' => 'Corde réglable avec compteur'],
            ['vendor' => 'Beauté Africaine', 'name' => 'Beurre de karité', 'price' => 5000, 'stock' => 50, 'delivery' => 'free', 'desc' => 'Beurre de karité bio 250g'],
            ['vendor' => 'Beauté Africaine', 'name' => 'Huile de ricin', 'price' => 3500, 'stock' => 60, 'delivery' => 'free', 'desc' => 'Huile de ricin pure 100ml'],
            ['vendor' => 'Beauté Africaine', 'name' => 'Savon noir', 'price' => 1500, 'stock' => 100, 'delivery' => 'free', 'desc' => 'Savon noir naturel exfoliant'],
            ['vendor' => 'Librairie Savoir', 'name' => 'Roman africain', 'price' => 8000, 'stock' => 15, 'delivery' => 'fixed', 'desc' => 'Roman policier africain'],
            ['vendor' => 'Librairie Savoir', 'name' => 'Cahier grand carreaux', 'price' => 1000, 'stock' => 200, 'delivery' => 'free', 'desc' => 'Cahier 96 pages'],
            ['vendor' => 'Librairie Savoir', 'name' => 'Stylo bille pack', 'price' => 1500, 'stock' => 150, 'delivery' => 'free', 'desc' => 'Pack de 5 stylos bleus'],
            ['vendor' => 'Jouets & Enfants', 'name' => 'Voiture télécommandée', 'price' => 25000, 'stock' => 10, 'delivery' => 'fixed', 'desc' => 'Voiture RC 4x4 avec télécommande'],
            ['vendor' => 'Jouets & Enfants', 'name' => 'Poupée traditionnelle', 'price' => 8000, 'stock' => 25, 'delivery' => 'free', 'desc' => 'Poupée en wax avec accessoires'],
            ['vendor' => 'Jouets & Enfants', 'name' => 'Jeu de construction', 'price' => 12000, 'stock' => 20, 'delivery' => 'fixed', 'desc' => 'Blocs de construction 100 pièces'],
            ['vendor' => 'Jeux Vidéo Store', 'name' => 'Manette PS4', 'price' => 55000, 'stock' => 7, 'delivery' => 'fixed', 'desc' => 'Manette DualShock 4 officielle'],
            ['vendor' => 'Jeux Vidéo Store', 'name' => 'FIFA 24', 'price' => 65000, 'stock' => 6, 'delivery' => 'fixed', 'desc' => 'Jeu FIFA 24 pour PS4'],
            ['vendor' => 'Jeux Vidéo Store', 'name' => 'Console rétro', 'price' => 35000, 'stock' => 12, 'delivery' => 'fixed', 'desc' => 'Console rétro 500 jeux intégrés'],
            ['vendor' => 'Art & Artisanat', 'name' => 'Masque bois', 'price' => 45000, 'stock' => 6, 'delivery' => 'fixed', 'desc' => 'Masque sculpté à la main'],
            ['vendor' => 'Art & Artisanat', 'name' => 'Panier tressé', 'price' => 12000, 'stock' => 18, 'delivery' => 'free', 'desc' => 'Panier en joncs fait main'],
        ];

        foreach ($productsData as $product) {
            $vendor = $vendors[$product['vendor']] ?? null;
            if (! $vendor) {
                continue;
            }
            Product::firstOrCreate(
                ['name' => $product['name'], 'vendor_id' => $vendor->id],
                [
                    'type' => 'physical',
                    'description' => $product['desc'],
                    'price' => $product['price'],
                    'commission_percent' => 0,
                    'stock' => $product['stock'],
                    'status' => 'actif',
                    'delivery_type' => $product['delivery'],
                    'delivery_fee' => $product['delivery'] === 'fixed' ? 1500 : 0,
                ]
            );
        }

        // Restaurants : menus et horaires
        $this->seedRestaurant($vendors['Restaurant Le Mandingue'], [
            'Entrées' => [
                ['name' => 'Salade de mangue', 'price' => 3500],
                ['name' => 'Accras de poisson', 'price' => 4000],
            ],
            'Plats' => [
                ['name' => 'Poulet braisé avec alloco', 'price' => 8500],
                ['name' => 'Poisson braisé', 'price' => 10000],
                ['name' => 'Riz gras au poulet', 'price' => 7000],
            ],
            'Desserts' => [
                ['name' => 'Fruits frais', 'price' => 2000],
            ],
            'Boissons' => [
                ['name' => 'Jus de bissap', 'price' => 1500],
                ['name' => 'Coca 33cl', 'price' => 1000],
            ],
        ]);

        $this->seedRestaurant($vendors['Restaurant Chez Kadi'], [
            'Entrées' => [
                ['name' => 'Soupe de légumes', 'price' => 3000],
                ['name' => 'Samoussas légumes', 'price' => 2500],
            ],
            'Plats' => [
                ['name' => 'Mafe au poulet', 'price' => 8000],
                ['name' => 'Thieboudienne', 'price' => 9000],
                ['name' => 'Yassa au poulet', 'price' => 8500],
            ],
            'Desserts' => [
                ['name' => 'Lakh', 'price' => 2500],
            ],
            'Boissons' => [
                ['name' => 'Jus de gingembre', 'price' => 1500],
                ['name' => 'Eau minérale', 'price' => 500],
            ],
        ]);
    }

    private function seedRestaurant(User $restaurant, array $menuData): void
    {
        foreach (range(0, 6) as $day) {
            RestaurantHour::firstOrCreate(
                ['restaurant_id' => $restaurant->id, 'day_of_week' => $day],
                [
                    'open_time' => '09:00',
                    'close_time' => '22:00',
                    'is_closed' => false,
                ]
            );
        }

        foreach ($menuData as $categoryName => $items) {
            $category = MenuCategory::firstOrCreate(
                ['restaurant_id' => $restaurant->id, 'name' => $categoryName],
                [
                    'slug' => Str::slug($categoryName),
                    'sort_order' => 0,
                    'is_active' => true,
                ]
            );

            foreach ($items as $item) {
                MenuItem::firstOrCreate(
                    ['restaurant_id' => $restaurant->id, 'name' => $item['name']],
                    [
                        'category_id' => $category->id,
                        'description' => $item['name'],
                        'price' => $item['price'],
                        'image_path' => 'products/default.jpg',
                        'is_available' => true,
                        'sort_order' => 0,
                    ]
                );
            }
        }
    }
}
