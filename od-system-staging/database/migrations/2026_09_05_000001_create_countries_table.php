<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('countries', function (Blueprint $table) {
            $table->id();
            $table->string('code', 2)->unique();
            $table->string('name');
            $table->string('currency_code', 3)->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        // Seed des pays d'Afrique de l'Ouest et quelques autres
        $countries = [
            ['code' => 'BJ', 'name' => 'Bénin',           'currency_code' => 'XOF'],
            ['code' => 'TG', 'name' => 'Togo',            'currency_code' => 'XOF'],
            ['code' => 'CI', 'name' => "Côte d'Ivoire",   'currency_code' => 'XOF'],
            ['code' => 'SN', 'name' => 'Sénégal',         'currency_code' => 'XOF'],
            ['code' => 'BF', 'name' => 'Burkina Faso',    'currency_code' => 'XOF'],
            ['code' => 'ML', 'name' => 'Mali',            'currency_code' => 'XOF'],
            ['code' => 'NE', 'name' => 'Niger',           'currency_code' => 'XOF'],
            ['code' => 'GN', 'name' => 'Guinée',          'currency_code' => 'XOF'],
            ['code' => 'CM', 'name' => 'Cameroun',        'currency_code' => 'XAF'],
            ['code' => 'NG', 'name' => 'Nigeria',         'currency_code' => 'NGN'],
            ['code' => 'GH', 'name' => 'Ghana',           'currency_code' => 'GHS'],
            ['code' => 'CD', 'name' => 'RD Congo',        'currency_code' => 'CDF'],
            ['code' => 'CG', 'name' => 'Congo',           'currency_code' => 'XAF'],
            ['code' => 'RW', 'name' => 'Rwanda',          'currency_code' => 'RWF'],
            ['code' => 'KE', 'name' => 'Kenya',           'currency_code' => 'KES'],
        ];

        foreach ($countries as $c) {
            DB::table('countries')->insert(array_merge($c, [
                'is_active'   => true,
                'created_at'  => now(),
                'updated_at'  => now(),
            ]));
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('countries');
    }
};
