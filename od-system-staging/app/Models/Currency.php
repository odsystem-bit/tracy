<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Currency extends Model
{
    protected $fillable = [
        'code',
        'name',
        'symbol',
        'rate_to_xof',
        'country_codes',
        'is_active',
    ];

    protected $casts = [
        'rate_to_xof' => 'float',
        'country_codes' => 'array',
        'is_active' => 'boolean',
    ];

    /**
     * Convertit un montant en XOF vers cette devise.
     */
    public function convertFromXof(float $amountXof): float
    {
        if ($this->rate_to_xof <= 0) {
            return $amountXof;
        }

        return round($amountXof / $this->rate_to_xof, 2);
    }

    /**
     * Convertit un montant de cette devise vers XOF.
     */
    public function convertToXof(float $amount): float
    {
        return round($amount * $this->rate_to_xof, 2);
    }

    /**
     * Formate un montant dans cette devise.
     */
    public function format(float $amount): string
    {
        $formatted = number_format($amount, 0, ',', ' ');

        return match ($this->code) {
            'XOF', 'XAF' => $formatted . ' ' . $this->symbol,
            'USD' => $this->symbol . $formatted,
            'EUR' => $formatted . ' ' . $this->symbol,
            default => $formatted . ' ' . $this->symbol,
        };
    }

    /**
     * Trouve la devise correspondant à un code pays.
     */
    public static function findByCountryCode(string $countryCode): ?self
    {
        return static::where('is_active', true)
            ->get()
            ->first(function ($currency) use ($countryCode) {
                return in_array(strtoupper($countryCode), $currency->country_codes ?? []);
            });
    }
}
