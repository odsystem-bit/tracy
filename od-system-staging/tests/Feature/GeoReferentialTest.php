<?php

namespace Tests\Feature;

use App\Models\Country;
use App\Models\Quartier;
use App\Models\ShopDeliveryQuartier;
use App\Models\User;
use App\Models\Ville;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class GeoReferentialTest extends TestCase
{
    use RefreshDatabase;

    /** @test */
    public function it_seeds_benin_villes(): void
    {
        $benin = Country::where('code', 'BJ')->first();
        $this->assertNotNull($benin, 'Le Bénin doit exister dans la table countries');

        $cotonou = Ville::where('name', 'Cotonou')->where('country_id', $benin->id)->first();
        $this->assertNotNull($cotonou, 'Cotonou doit être seedée');
        $this->assertEquals('Littoral', $cotonou->department_name);
    }

    /** @test */
    public function it_seeds_benin_quartiers(): void
    {
        $cotonou = Ville::where('name', 'Cotonou')->first();
        $this->assertNotNull($cotonou);

        $ganhi = Quartier::where('name', 'Ganhi')->where('ville_id', $cotonou->id)->first();
        $this->assertNotNull($ganhi, 'Le quartier Ganhi doit être seedé à Cotonou');
        $this->assertNotNull($ganhi->arrondissement_name);
    }

    /** @test */
    public function it_seeds_multiple_villes_and_quartiers(): void
    {
        $benin = Country::where('code', 'BJ')->first();
        $villeCount = Ville::where('country_id', $benin->id)->count();
        $this->assertGreaterThan(10, $villeCount, 'Au moins 10 villes doivent être seedées');

        $quartierCount = Quartier::count();
        $this->assertGreaterThan(20, $quartierCount, 'Au moins 20 quartiers doivent être seedés');
    }

    /** @test */
    public function it_resolves_quartier_by_name(): void
    {
        $response = $this->getJson('/api/geo/resolve?query=Ganhi');

        $response->assertStatus(200)
            ->assertJson([
                'found' => true,
                'type'  => 'quartier',
                'name'  => 'Ganhi',
            ])
            ->assertJsonStructure([
                'found',
                'type',
                'id',
                'name',
                'arrondissement',
                'ville_id',
                'ville_name',
                'department',
            ]);
    }

    /** @test */
    public function it_resolves_quartier_case_insensitive_and_accents(): void
    {
        $response = $this->getJson('/api/geo/resolve?query=dantokpa');

        $response->assertStatus(200)
            ->assertJson([
                'found' => true,
                'type'  => 'quartier',
                'name'  => 'Dantokpa',
            ]);
    }

    /** @test */
    public function it_resolves_ville_as_fallback(): void
    {
        $response = $this->getJson('/api/geo/resolve?query=Parakou');

        $response->assertStatus(200)
            ->assertJson([
                'found' => true,
                'type'  => 'ville',
                'name'  => 'Parakou',
            ]);
    }

    /** @test */
    public function it_returns_404_for_unknown_query(): void
    {
        $response = $this->getJson('/api/geo/resolve?query=VilleInexistante123');

        $response->assertStatus(404)
            ->assertJson([
                'found' => false,
            ]);
    }

    /** @test */
    public function it_returns_quartiers_for_a_ville(): void
    {
        $cotonou = Ville::where('name', 'Cotonou')->first();

        $response = $this->getJson("/api/villes/{$cotonou->id}/quartiers");

        $response->assertStatus(200)
            ->assertJsonStructure([
                'ville' => ['id', 'name', 'department'],
                'quartiers' => [['id', 'name', 'arrondissement_name']],
            ])
            ->assertJsonPath('ville.name', 'Cotonou');
    }

    /** @test */
    public function it_returns_404_for_unknown_ville(): void
    {
        $response = $this->getJson('/api/villes/99999/quartiers');

        $response->assertStatus(404);
    }

    /** @test */
    public function it_creates_delivery_quartier_for_shop(): void
    {
        $user = User::factory()->create(['role' => 'vendor']);
        $quartier = Quartier::first();

        $response = $this->withHeader('X-Bot-Api-Key', env('BOT_API_SECRET', 'test-bot-key'))
            ->postJson("/bot/stores/{$user->id}/delivery-quartiers", [
                'quartier_ids' => [$quartier->id],
            ]);

        $response->assertStatus(200)
            ->assertJson(['success' => true]);

        $this->assertDatabaseHas('shop_delivery_quartiers', [
            'shop_id'     => $user->id,
            'quartier_id' => $quartier->id,
        ]);

        $user->refresh();
        $this->assertEquals('quartiers', $user->delivery_mode);
    }

    /** @test */
    public function it_adds_all_quartiers_for_a_ville(): void
    {
        $user = User::factory()->create(['role' => 'vendor']);
        $cotonou = Ville::where('name', 'Cotonou')->first();
        $cotonouQuartierIds = Quartier::where('ville_id', $cotonou->id)->pluck('id')->toArray();

        $response = $this->withHeader('X-Bot-Api-Key', env('BOT_API_SECRET', 'test-bot-key'))
            ->postJson("/bot/stores/{$user->id}/delivery-quartiers", [
                'ville_id' => $cotonou->id,
            ]);

        $response->assertStatus(200)
            ->assertJson(['success' => true]);

        $addedCount = ShopDeliveryQuartier::where('shop_id', $user->id)->count();
        $this->assertEquals(count($cotonouQuartierIds), $addedCount);
    }

    /** @test */
    public function it_adds_all_quartiers_except_excluded(): void
    {
        $user = User::factory()->create(['role' => 'vendor']);
        $cotonou = Ville::where('name', 'Cotonou')->first();
        $cotonouQuartiers = Quartier::where('ville_id', $cotonou->id)->get();
        $excludeId = $cotonouQuartiers->first()->id;

        $response = $this->withHeader('X-Bot-Api-Key', env('BOT_API_SECRET', 'test-bot-key'))
            ->postJson("/bot/stores/{$user->id}/delivery-quartiers", [
                'ville_id'             => $cotonou->id,
                'exclude_quartier_ids' => [$excludeId],
            ]);

        $response->assertStatus(200)
            ->assertJson(['success' => true]);

        $this->assertDatabaseMissing('shop_delivery_quartiers', [
            'shop_id'     => $user->id,
            'quartier_id' => $excludeId,
        ]);

        $addedCount = ShopDeliveryQuartier::where('shop_id', $user->id)->count();
        $this->assertEquals($cotonouQuartiers->count() - 1, $addedCount);
    }

    /** @test */
    public function it_removes_a_delivery_quartier(): void
    {
        $user = User::factory()->create(['role' => 'vendor']);
        $quartier = Quartier::first();

        ShopDeliveryQuartier::create([
            'shop_id'     => $user->id,
            'quartier_id' => $quartier->id,
        ]);

        $response = $this->withHeader('X-Bot-Api-Key', env('BOT_API_SECRET', 'test-bot-key'))
            ->deleteJson("/bot/stores/{$user->id}/delivery-quartiers/{$quartier->id}");

        $response->assertStatus(200)
            ->assertJson(['success' => true]);

        $this->assertDatabaseMissing('shop_delivery_quartiers', [
            'shop_id'     => $user->id,
            'quartier_id' => $quartier->id,
        ]);
    }

    /** @test */
    public function it_reverts_to_pickup_only_when_no_quartiers_left(): void
    {
        $user = User::factory()->create([
            'role'          => 'vendor',
            'delivery_mode' => 'quartiers',
        ]);
        $quartier = Quartier::first();

        ShopDeliveryQuartier::create([
            'shop_id'     => $user->id,
            'quartier_id' => $quartier->id,
        ]);

        $this->withHeader('X-Bot-Api-Key', env('BOT_API_SECRET', 'test-bot-key'))
            ->deleteJson("/bot/stores/{$user->id}/delivery-quartiers/{$quartier->id}");

        $user->refresh();
        $this->assertEquals('pickup_only', $user->delivery_mode);
    }

    /** @test */
    public function it_gets_delivery_quartiers_for_shop(): void
    {
        $user = User::factory()->create(['role' => 'vendor']);
        $quartiers = Quartier::limit(3)->get();

        foreach ($quartiers as $q) {
            ShopDeliveryQuartier::create([
                'shop_id'     => $user->id,
                'quartier_id' => $q->id,
            ]);
        }

        $response = $this->withHeader('X-Bot-Api-Key', env('BOT_API_SECRET', 'test-bot-key'))
            ->getJson("/bot/stores/{$user->id}/delivery-quartiers");

        $response->assertStatus(200)
            ->assertJsonPath('store_id', (string) $user->id)
            ->assertJsonPath('delivery_mode', 'pickup_only')
            ->assertJsonCount(3, 'quartiers');
    }
}
