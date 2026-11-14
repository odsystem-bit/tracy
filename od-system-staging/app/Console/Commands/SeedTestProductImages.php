<?php

declare(strict_types=1);

namespace App\Console\Commands;

use App\Models\Product;
use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Storage;

class SeedTestProductImages extends Command
{
    protected $signature = 'products:seed-test-images';

    protected $description = 'Génère des images placeholder pour les produits de test sans image_path (idempotente).';

    /**
     * Produits cibles du seeder BoutiqueProductSeeder.
     * On prend un échantillon varié : téléphones, accessoires, vêtements, électroménager, etc.
     */
    private const TARGET_PRODUCT_NAMES = [
        'Téléphone Samsung A15',
        'Coque Samsung A15',
        'Chargeur USB-C 25W',
        'iPhone 12 Pro',
        'Écouteurs Bluetooth',
        'Xiaomi Redmi Note 12',
        'Powerbank 20000mAh',
        'Tecno Spark 10 Pro',
        'Câble USB-C 2m',
        'Ordinateur portable HP',
        'Robe longue wax',
        'Chemise homme coton',
        'Baskets running',
        'Collier perles',
        'Lampe design',
        'Télévision 32 pouces',
        'Manette PS4',
        'Beurre de karité',
        'Masque bois',
        'Voiture télécommandée',
    ];

    /**
     * Couleurs par catégorie de produit pour des placeholders visuellement distincts.
     */
    private function getColorForProduct(string $name): string
    {
        $nameLower = mb_strtolower($name);
        if (str_contains($nameLower, 'téléphone') || str_contains($nameLower, 'iphone') || str_contains($nameLower, 'tecno') || str_contains($nameLower, 'xiaomi') || str_contains($nameLower, 'redmi')) {
            return '#1a56db'; // bleu
        }
        if (str_contains($nameLower, 'coque') || str_contains($nameLower, 'chargeur') || str_contains($nameLower, 'câble') || str_contains($nameLower, 'cable')) {
            return '#6b7280'; // gris
        }
        if (str_contains($nameLower, 'écouteur') || str_contains($nameLower, 'ecouteur') || str_contains($nameLower, 'casque')) {
            return '#7c3aed'; // violet
        }
        if (str_contains($nameLower, 'powerbank') || str_contains($nameLower, 'batterie')) {
            return '#f59e0b'; // orange
        }
        if (str_contains($nameLower, 'ordinateur') || str_contains($nameLower, 'laptop') || str_contains($nameLower, 'souris') || str_contains($nameLower, 'clavier')) {
            return '#059669'; // vert
        }
        if (str_contains($nameLower, 'robe') || str_contains($nameLower, 'chemise') || str_contains($nameLower, 'pantalon') || str_contains($nameLower, 'boubou') || str_contains($nameLower, 't-shirt')) {
            return '#db2777'; // rose
        }
        if (str_contains($nameLower, 'basket') || str_contains($nameLower, 'sandale') || str_contains($nameLower, 'mocassin') || str_contains($nameLower, 'bottine')) {
            return '#92400e'; // marron
        }
        if (str_contains($nameLower, 'collier') || str_contains($nameLower, 'bracelet') || str_contains($nameLower, 'boucle') || str_contains($nameLower, 'bijoux')) {
            return '#facc15'; // jaune doré
        }
        if (str_contains($nameLower, 'télévision') || str_contains($nameLower, 'television') || str_contains($nameLower, 'réfrigérateur') || str_contains($nameLower, 'ventilateur') || str_contains($nameLower, 'fer') || str_contains($nameLower, 'micro-ondes')) {
            return '#374151'; // gris foncé
        }
        if (str_contains($nameLower, 'manette') || str_contains($nameLower, 'console') || str_contains($nameLower, 'fifa') || str_contains($nameLower, 'jeu')) {
            return '#0ea5e9'; // bleu clair
        }
        if (str_contains($nameLower, 'beurre') || str_contains($nameLower, 'huile') || str_contains($nameLower, 'savon') || str_contains($nameLower, 'cosmétique') || str_contains($nameLower, 'cosmetique')) {
            return '#84cc16'; // vert clair
        }
        if (str_contains($nameLower, 'masque') || str_contains($nameLower, 'panier') || str_contains($nameLower, 'artisanat')) {
            return '#b45309'; // terre
        }
        if (str_contains($nameLower, 'voiture') || str_contains($nameLower, 'poupée') || str_contains($nameLower, 'construction') || str_contains($nameLower, 'jouet')) {
            return '#ef4444'; // rouge
        }
        return '#0f766e'; // teal par défaut
    }

    private function generatePlaceholderSvg(string $productName, string $color): string
    {
        $initials = collect(explode(' ', $productName))
            ->filter(fn ($w) => mb_strlen($w) >= 2 && !in_array(mb_strtolower($w), ['de', 'du', 'le', 'la', 'les', 'à', 'a', 'au', 'aux', 'sur', 'et']))
            ->take(2)
            ->map(fn ($w) => mb_strtoupper(mb_substr($w, 0, 1)))
            ->implode('');

        if ($initials === '') {
            $initials = mb_strtoupper(mb_substr($productName, 0, 2));
        }

        $escapedName = htmlspecialchars($productName, ENT_XML1 | ENT_QUOTES, 'UTF-8');
        $escapedInitials = htmlspecialchars($initials, ENT_XML1 | ENT_QUOTES, 'UTF-8');

        return <<<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="{$color}"/>
  <rect x="0" y="0" width="400" height="300" fill="url(#grad)" opacity="0.15"/>
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#ffffff;stop-opacity:0.2"/>
      <stop offset="100%" style="stop-color:#000000;stop-opacity:0.1"/>
    </linearGradient>
  </defs>
  <circle cx="200" cy="120" r="55" fill="rgba(255,255,255,0.2)"/>
  <text x="200" y="135" font-family="Arial,sans-serif" font-size="36" font-weight="bold" fill="rgba(255,255,255,0.9)" text-anchor="middle">{$escapedInitials}</text>
  <text x="200" y="220" font-family="Arial,sans-serif" font-size="16" fill="rgba(255,255,255,0.85)" text-anchor="middle">{$escapedName}</text>
  <text x="200" y="245" font-family="Arial,sans-serif" font-size="11" fill="rgba(255,255,255,0.5)" text-anchor="middle">Mantota</text>
</svg>
SVG;
    }

    private function generatePlaceholderShopSvg(string $shopName, string $color): string
    {
        $initials = collect(explode(' ', $shopName))
            ->filter(fn ($w) => mb_strlen($w) >= 2 && !in_array(mb_strtolower($w), ['de', 'du', 'le', 'la', 'les', 'à', 'a', 'au', 'aux', 'sur', 'et', '&']))
            ->take(2)
            ->map(fn ($w) => mb_strtoupper(mb_substr($w, 0, 1)))
            ->implode('');

        if ($initials === '') {
            $initials = mb_strtoupper(mb_substr($shopName, 0, 2));
        }

        $escapedInitials = htmlspecialchars($initials, ENT_XML1 | ENT_QUOTES, 'UTF-8');

        return <<<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <rect width="200" height="200" fill="{$color}"/>
  <circle cx="100" cy="100" r="60" fill="rgba(255,255,255,0.15)"/>
  <text x="100" y="115" font-family="Arial,sans-serif" font-size="42" font-weight="bold" fill="rgba(255,255,255,0.95)" text-anchor="middle">{$escapedInitials}</text>
</svg>
SVG;
    }

    public function handle(): int
    {
        $disk = Storage::disk('public');

        // S'assurer que le dossier products/ existe
        if (! $disk->exists('products')) {
            $disk->makeDirectory('products');
        }
        if (! $disk->exists('shops')) {
            $disk->makeDirectory('shops');
        }

        $updated = 0;
        $skipped = 0;

        foreach (self::TARGET_PRODUCT_NAMES as $name) {
            // Trouver le produit par nom (firstOrCreate du seeder utilise name + vendor_id)
            $products = Product::where('name', $name)->get();

            if ($products->isEmpty()) {
                $this->warn("  Produit introuvable : {$name}");
                continue;
            }

            foreach ($products as $product) {
                // Ne pas toucher aux produits qui ont déjà une image
                if ($product->image_path) {
                    $skipped++;
                    continue;
                }

                // Générer le nom de fichier (idempotente : basé sur l'ID produit)
                $filename = "products/test-placeholder-{$product->id}.svg";
                $relativePath = $filename;

                // Si le fichier existe déjà, on passe (idempotente)
                if ($disk->exists($relativePath)) {
                    $product->update(['image_path' => $relativePath]);
                    $updated++;
                    $this->info("  ✓ {$product->name} (ID: {$product->id}) → image déjà présente, image_path mis à jour");
                    continue;
                }

                // Générer l'image SVG
                $color = $this->getColorForProduct($product->name);
                $svg = $this->generatePlaceholderSvg($product->name, $color);

                $disk->put($relativePath, $svg);
                $product->update(['image_path' => $relativePath]);
                $updated++;

                $this->info("  ✓ {$product->name} (ID: {$product->id}) → {$relativePath}");
            }
        }

        $this->newLine();
        $this->info("Terminé : {$updated} produit(s) mis à jour, {$skipped} produit(s) ignorés (image_path déjà renseigné).");

        // ── Logos boutique (vendeurs de test) ──
        $shopUpdated = 0;
        $shopSkipped = 0;

        $vendors = User::where('role', 'vendor')
            ->whereNotNull('shop_name')
            ->where('shop_name', '!=', '')
            ->get();

        foreach ($vendors as $vendor) {
            if ($vendor->shop_logo_path) {
                $shopSkipped++;
                continue;
            }

            $relativePath = "shops/test-logo-{$vendor->id}.svg";

            if ($disk->exists($relativePath)) {
                $vendor->update(['shop_logo_path' => $relativePath]);
                $shopUpdated++;
                $this->info("  ✓ {$vendor->shop_name} (ID: {$vendor->id}) → logo déjà présent, shop_logo_path mis à jour");
                continue;
            }

            $color = $this->getColorForProduct($vendor->shop_name);
            $svg = $this->generatePlaceholderShopSvg($vendor->shop_name, $color);

            $disk->put($relativePath, $svg);
            $vendor->update(['shop_logo_path' => $relativePath]);
            $shopUpdated++;

            $this->info("  ✓ {$vendor->shop_name} (ID: {$vendor->id}) → {$relativePath}");
        }

        $this->newLine();
        $this->info("Terminé : {$shopUpdated} boutique(s) mise(s) à jour, {$shopSkipped} boutique(s) ignorée(s) (shop_logo_path déjà renseigné).");

        // Afficher le récapitulatif produits
        $this->newLine();
        $this->info('── Récapitulatif des produits avec image ──');
        $products = Product::whereIn('name', self::TARGET_PRODUCT_NAMES)
            ->whereNotNull('image_path')
            ->get();

        $tableData = [];
        foreach ($products as $p) {
            $tableData[] = [
                $p->id,
                $p->name,
                $p->image_path,
                asset('storage/' . $p->image_path),
            ];
        }
        $this->table(['ID', 'Nom', 'image_path', 'image_url'], $tableData);

        // Afficher le récapitulatif boutiques
        $this->newLine();
        $this->info('── Récapitulatif des boutiques avec logo ──');
        $vendorsWithLogo = User::where('role', 'vendor')
            ->whereNotNull('shop_logo_path')
            ->get();

        $shopTableData = [];
        foreach ($vendorsWithLogo as $v) {
            $shopTableData[] = [
                $v->id,
                $v->shop_name,
                $v->shop_logo_path,
                asset('storage/' . $v->shop_logo_path),
            ];
        }
        $this->table(['ID', 'Boutique', 'shop_logo_path', 'image_url'], $shopTableData);

        return self::SUCCESS;
    }
}
