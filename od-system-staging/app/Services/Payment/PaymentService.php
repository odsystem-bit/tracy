<?php

declare(strict_types=1);

namespace App\Services\Payment;

use App\Models\Gateway;
use Illuminate\Support\Facades\Http;
use App\Models\Order;
use Illuminate\Support\Facades\Log;

/**
 * PaymentService — Passerelle de paiement unique pour Mantota / Tracy IA.
 *
 * Fournisseur : Moneroo (https://moneroo.io)
 * Fonctions couvertes :
 *  - Paiement de commandes (checkout invité)
 *  - Dépôt sur wallet vendeur/créateur
 *  - Retrait (payout) Mobile Money
 *  - Webhook de confirmation
 *  - Vérification transaction/payout
 *
 * Toute la configuration est centralisée dans la table gateways (slug=moneroo)
 * avec fallback sur config/services.php pour la première installation.
 */
final class PaymentService
{
    private const string DEFAULT_API_BASE = 'https://api.moneroo.io/v1';
    private const string DEFAULT_CURRENCY = 'XOF';

    private const float DEFAULT_PAYMENT_FEE_PERCENT = 2.0;
    private const float DEFAULT_PAYOUT_FEE_PERCENT  = 1.0;
    private const float DEFAULT_MARKUP_PERCENT      = 2.0;

    private array $config;

    public function __construct()
    {
        $this->config = self::resolveApiConfig();
    }

    /**
     * Résout la configuration Moneroo.
     * Priorité : table gateways > settings > config/services.php
     */
    public static function resolveApiConfig(): array
    {
        $gateway = Gateway::where('slug', 'moneroo')->first();

        $apiUrl = (string) (($gateway?->extra_config ?? [])['api_url'] ?? config('services.moneroo.api_url', self::DEFAULT_API_BASE));
        if ($apiUrl === '') {
            $apiUrl = self::DEFAULT_API_BASE;
        }

        $secretKey = (string) ($gateway?->secret_key ?? config('services.moneroo.secret_key', ''));
        $publicKey = (string) ($gateway?->public_key ?? config('services.moneroo.public_key', ''));
        $webhookSecret = (string) ($gateway?->webhook_secret ?? config('services.moneroo.webhook_secret', ''));

        return [
            'api_url'        => rtrim($apiUrl, '/'),
            'secret_key'     => $secretKey,
            'public_key'     => $publicKey,
            'webhook_secret' => $webhookSecret,
            'currency'       => config('services.moneroo.currency', self::DEFAULT_CURRENCY),
            'environment'    => $gateway?->environment ?? config('services.moneroo.environment', 'sandbox'),
        ];
    }

    public function isConfigured(): bool
    {
        return $this->config['secret_key'] !== '' && $this->config['api_url'] !== '';
    }

    /**
     * Initialiser un paiement.
     *
     * @param array{
     *   amount: int|float,
     *   description: string,
     *   customer: array{first_name:string, last_name?:string, email:string, phone?:string},
     *   return_url: string,
     *   metadata?: array,
     *   methods?: string[],
     *   currency?: string
     * } $payload
     *
     * @return array{success:bool, id?:string, checkout_url?:string, message?:string}
     */
    public function initializePayment(array $payload): array
    {
        if (! $this->isConfigured()) {
            return ['success' => false, 'message' => 'Configuration Moneroo manquante.'];
        }

        $body = [
            'amount'      => (int) round((float) $payload['amount']),
            'currency'    => $payload['currency'] ?? $this->config['currency'],
            'description' => $payload['description'],
            'customer'    => [
                'email'       => $payload['customer']['email'] ?? '',
                'first_name'  => $payload['customer']['first_name'] ?? '',
                'last_name'   => $payload['customer']['last_name'] ?? '',
            ],
            'return_url'  => $payload['return_url'],
            'metadata'    => $payload['metadata'] ?? [],
        ];

        if (! empty($payload['customer']['phone'])) {
            $body['customer']['phone'] = $payload['customer']['phone'];
        }

        if (! empty($payload['methods']) && is_array($payload['methods'])) {
            $body['methods'] = $payload['methods'];
        }

        try {
            $response = Http::withHeaders($this->apiHeaders())
                ->connectTimeout(10)
                ->timeout(60)
                ->post("{$this->config['api_url']}/payments/initialize", $body);

            if (! $response->successful()) {
                Log::error('Moneroo initialize payment failed', [
                    'status' => $response->status(),
                    'body'   => $response->body(),
                ]);

                return [
                    'success' => false,
                    'message' => 'Erreur Moneroo ' . $response->status() . ' : ' . $response->body(),
                ];
            }

            $data = $response->json('data') ?? [];

            if (empty($data['checkout_url']) || empty($data['id'])) {
                return ['success' => false, 'message' => 'Réponse Moneroo invalide : checkout_url ou id manquant.'];
            }

            return [
                'success'      => true,
                'id'           => (string) $data['id'],
                'checkout_url' => (string) $data['checkout_url'],
            ];
        } catch (\Throwable $e) {
            Log::error('Moneroo initialize payment exception', ['error' => $e->getMessage()]);

            return ['success' => false, 'message' => 'Exception Moneroo : ' . $e->getMessage()];
        }
    }

    /**
     * Vérifier le statut d'un paiement.
     *
     * @return array{success:bool, status?:'success'|'pending'|'failed', amount?:float, currency?:string, message?:string}
     */
    public function verifyPayment(string $paymentId): array
    {
        if (! $this->isConfigured()) {
            return ['success' => false, 'message' => 'Configuration Moneroo manquante.'];
        }

        try {
            $response = Http::withHeaders($this->apiHeaders())
                ->connectTimeout(10)
                ->timeout(30)
                ->get("{$this->config['api_url']}/payments/{$paymentId}/verify");

            if (! $response->successful()) {
                return ['success' => false, 'message' => 'Erreur vérification Moneroo : ' . $response->status()];
            }

            $data = $response->json('data') ?? [];
            $status = strtolower((string) ($data['status'] ?? 'pending'));

            return [
                'success'  => true,
                'status'   => in_array($status, ['success', 'pending', 'failed'], true) ? $status : 'pending',
                'amount'   => (float) ($data['amount'] ?? 0),
                'currency' => (string) ($data['currency']['code'] ?? $data['currency'] ?? $this->config['currency']),
            ];
        } catch (\Throwable $e) {
            Log::error('Moneroo verify payment exception', ['payment_id' => $paymentId, 'error' => $e->getMessage()]);

            return ['success' => false, 'message' => 'Exception vérification : ' . $e->getMessage()];
        }
    }

    /**
     * Initialiser un retrait (payout) Mobile Money.
     *
     * @param array{
     *   amount: int|float,
     *   description: string,
     *   customer: array{email:string, first_name:string, last_name?:string, phone?:string},
     *   method: string,
     *   recipient: array,
     *   metadata?: array,
     *   currency?: string
     * } $payload
     *
     * @return array{success:bool, id?:string, message?:string}
     */
    public function initializePayout(array $payload): array
    {
        if (! $this->isConfigured()) {
            return ['success' => false, 'message' => 'Configuration Moneroo manquante.'];
        }

        $body = [
            'amount'      => (int) round((float) $payload['amount']),
            'currency'    => $payload['currency'] ?? $this->config['currency'],
            'description' => $payload['description'],
            'customer'    => [
                'email'       => $payload['customer']['email'] ?? '',
                'first_name'  => $payload['customer']['first_name'] ?? '',
                'last_name'   => $payload['customer']['last_name'] ?? '',
            ],
            'method'      => $payload['method'],
            'recipient'   => $payload['recipient'] ?? [],
            'metadata'    => $payload['metadata'] ?? [],
        ];

        try {
            $response = Http::withHeaders($this->apiHeaders())
                ->connectTimeout(10)
                ->timeout(60)
                ->post("{$this->config['api_url']}/payouts/initialize", $body);

            if (! $response->successful()) {
                Log::error('Moneroo initialize payout failed', [
                    'status' => $response->status(),
                    'body'   => $response->body(),
                ]);

                return [
                    'success' => false,
                    'message' => 'Erreur payout Moneroo ' . $response->status() . ' : ' . $response->body(),
                ];
            }

            $data = $response->json('data') ?? [];

            if (empty($data['id'])) {
                return ['success' => false, 'message' => 'Réponse payout Moneroo invalide : id manquant.'];
            }

            return [
                'success' => true,
                'id'      => (string) $data['id'],
            ];
        } catch (\Throwable $e) {
            Log::error('Moneroo initialize payout exception', ['error' => $e->getMessage()]);

            return ['success' => false, 'message' => 'Exception payout : ' . $e->getMessage()];
        }
    }

    /**
     * Vérifier le statut d'un payout.
     *
     * @return array{success:bool, status?:'success'|'pending'|'failed', message?:string}
     */
    public function verifyPayout(string $payoutId): array
    {
        if (! $this->isConfigured()) {
            return ['success' => false, 'message' => 'Configuration Moneroo manquante.'];
        }

        try {
            $response = Http::withHeaders($this->apiHeaders())
                ->connectTimeout(10)
                ->timeout(30)
                ->get("{$this->config['api_url']}/payouts/{$payoutId}/verify");

            if (! $response->successful()) {
                return ['success' => false, 'message' => 'Erreur vérification payout : ' . $response->status()];
            }

            $data = $response->json('data') ?? [];
            $status = strtolower((string) ($data['status'] ?? 'pending'));

            return [
                'success' => true,
                'status'  => in_array($status, ['success', 'pending', 'failed'], true) ? $status : 'pending',
            ];
        } catch (\Throwable $e) {
            Log::error('Moneroo verify payout exception', ['payout_id' => $payoutId, 'error' => $e->getMessage()]);

            return ['success' => false, 'message' => 'Exception vérification payout : ' . $e->getMessage()];
        }
    }

    /**
     * Vérifier la signature HMAC-SHA256 d'un webhook Moneroo.
     */
    public function verifyWebhookSignature(string $payload, string $signature): bool
    {
        $secret = $this->config['webhook_secret'];
        if ($secret === '') {
            return false;
        }

        $expected = hash_hmac('sha256', $payload, $secret);

        return hash_equals($expected, $signature);
    }

    /**
     * Décomposition financière d'un dépôt.
     */
    public function calculateDeposit(float $targetAmount): array
    {
        $feePercent    = (float) mantota_setting('moneroo_payment_fee_percent', self::DEFAULT_PAYMENT_FEE_PERCENT);
        $markupPercent = (float) mantota_setting('deposit_markup_percent', self::DEFAULT_MARKUP_PERCENT);

        $markup       = round($targetAmount * ($markupPercent / 100), 2);
        $subtotal     = round($targetAmount + $markup, 2);
        $amountTotal  = round($subtotal / (1 - ($feePercent / 100)), 2);
        $gatewayFee   = round($amountTotal - $subtotal, 2);

        return [
            'target_amount'  => round($targetAmount, 2),
            'gateway_fee'    => $gatewayFee,
            'mantota_markup' => $markup,
            'amount_total'   => $amountTotal,
        ];
    }

    /**
     * Décomposition financière d'un retrait.
     */
    public function calculateWithdrawal(float $requestedAmount): array
    {
        $commissionRate = (float) mantota_setting('withdrawal_fee_percent', 20) / 100;
        $payoutFeePercent = (float) mantota_setting('moneroo_payout_fee_percent', self::DEFAULT_PAYOUT_FEE_PERCENT);

        $platformCommission = round($requestedAmount * $commissionRate, 2);
        $afterCommission    = round($requestedAmount - $platformCommission, 2);
        $gatewayFee         = round($afterCommission * ($payoutFeePercent / 100), 2);
        $netPayout          = round($afterCommission - $gatewayFee, 2);

        return [
            'requested_amount'   => round($requestedAmount, 2),
            'mantota_commission' => $platformCommission,
            'gateway_fee'        => $gatewayFee,
            'net_payout'         => $netPayout,
        ];
    }

    /**
     * Détecte la méthode Moneroo Mobile Money à partir du pays et du numéro.
     *
     * @return array{0:string,1:string,2:string}|null [method, recipient_key, recipient_value]
     */
    public static function resolveMobileMoneyMethod(string $countryCode, string $network): ?array
    {
        $mapping = [
            'BJ' => [
                'MTN'     => ['mtn_bj', 'msisdn'],
                'MOOV'    => ['moov_bj', 'msisdn'],
                'CELTIIS' => ['moov_bj', 'msisdn'],
            ],
            'TG' => [
                'TMONEY' => ['togocel', 'msisdn'],
                'FLOOZ'  => ['moov_tg', 'msisdn'],
            ],
            'CI' => [
                'MTN'    => ['mtn_ci', 'msisdn'],
                'MOOV'   => ['moov_ci', 'msisdn'],
                'ORANGE' => ['orange_ci', 'msisdn'],
                'WAVE'   => ['wave_ci', 'msisdn'],
            ],
            'SN' => [
                'ORANGE'  => ['orange_sn', 'msisdn'],
                'WAVE'    => ['wave_sn', 'msisdn'],
                'FREE'    => ['freemoney_sn', 'msisdn'],
                'E-MONEY' => ['e_money_sn', 'msisdn'],
                'WIZALL'  => ['wizall_sn', 'msisdn'],
            ],
            'BF' => [
                'ORANGE' => ['orange_bf', 'msisdn'],
                'MOOV'   => ['moov_bf', 'msisdn'],
            ],
            'ML' => [
                'MOOV'      => ['moov_ml', 'msisdn'],
                'ORANGE'    => ['orange_ml', 'msisdn'],
                'MOBI_CASH' => ['mobi_cash_ml', 'msisdn'],
            ],
        ];

        $countryCode = strtoupper($countryCode);
        $network     = strtoupper($network);

        return $mapping[$countryCode][$network] ?? null;
    }

    public static function normalizePhone(string $phone, string $countryCode = 'BJ'): ?string
    {
        $digits = preg_replace('/[^0-9]/', '', $phone);
        if ($digits === null || strlen($digits) < 8) {
            return null;
        }

        $countryCode = strtoupper($countryCode);
        $prefixes = [
            'BJ' => ['229'],
            'TG' => ['228'],
            'CI' => ['225'],
            'SN' => ['221'],
            'BF' => ['226'],
            'ML' => ['223'],
        ];

        foreach ($prefixes[$countryCode] ?? [] as $prefix) {
            if (str_starts_with($digits, $prefix)) {
                return $digits;
            }
        }

        $defaultPrefix = $prefixes[$countryCode][0] ?? null;
        if ($defaultPrefix) {
            return $defaultPrefix . $digits;
        }

        return null;
    }

    public static function detectNetwork(string $phone, string $countryCode = 'BJ'): ?string
    {
        $normalized = self::normalizePhone($phone, $countryCode);
        if (! $normalized) {
            return null;
        }

        $countryCode = strtoupper($countryCode);

        if ($countryCode === 'BJ' && str_starts_with($normalized, '229')) {
            $local = substr($normalized, 3);
            $prefixes = [
                'MTN'   => ['52', '53', '54', '55', '56', '57', '58', '59', '61', '62', '63', '64', '65', '68', '90', '91', '92', '93', '94', '95', '96', '97', '98'],
                'MOOV'  => ['50', '51', '60', '66', '67', '69', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89'],
                'CELTIIS' => ['40', '41', '42', '43', '44', '45', '46', '47', '48', '49'],
            ];
            $firstTwo = substr($local, 0, 2);
            foreach ($prefixes as $network => $networkPrefixes) {
                if (in_array($firstTwo, $networkPrefixes, true)) {
                    return $network;
                }
            }
        }

        if ($countryCode === 'TG' && str_starts_with($normalized, '228')) {
            $local = substr($normalized, 3);
            $firstTwo = substr($local, 0, 2);

            return match ($firstTwo) {
                '70', '90', '91', '92', '93', '96' => 'TMONEY',
                '79', '97', '98', '99' => 'FLOOZ',
                default => null,
            };
        }

        if ($countryCode === 'CI' && str_starts_with($normalized, '225')) {
            $local = substr($normalized, 3);
            $firstTwo = substr($local, 0, 2);

            return match ($firstTwo) {
                '07', '08', '09', '27', '57', '67', '77' => 'MTN',
                '01', '02', '03', '05', '06', '65', '66' => 'MOOV',
                '07' => 'ORANGE',
                default => null,
            };
        }

        if ($countryCode === 'SN' && str_starts_with($normalized, '221')) {
            $local = substr($normalized, 3);
            $firstTwo = substr($local, 0, 2);

            return match ($firstTwo) {
                '77', '78' => 'ORANGE',
                '76', '70' => 'FREE',
                '75' => 'WAVE',
                default => null,
            };
        }

        return null;
    }

    /**
     * Tente un remboursement client via un payout Moneroo sur le numero d'origine.
     *
     * @return array{success:bool, id?:string, message?:string}
     */
    public function refundOrder(Order $order, float $amount, string $phone, string $countryCode): array
    {
        if (! $this->isConfigured()) {
            return ['success' => false, 'message' => 'Configuration Moneroo manquante.'];
        }

        $network = self::detectNetwork($phone, $countryCode);
        if (! $network) {
            return ['success' => false, 'message' => 'Reseau mobile non detecte pour le remboursement.'];
        }

        $method = self::resolveMobileMoneyMethod($countryCode, $network);
        if (! $method) {
            return ['success' => false, 'message' => 'Methode Mobile Money non supportee pour le remboursement.'];
        }

        $normalizedPhone = self::normalizePhone($phone, $countryCode);
        if (! $normalizedPhone) {
            return ['success' => false, 'message' => 'Numero de telephone invalide pour le remboursement.'];
        }

        return $this->initializePayout([
            'amount'      => (int) round($amount),
            'currency'    => $this->config['currency'],
            'description' => 'Remboursement commande ' . ($order->reference ?? $order->id),
            'customer'    => [
                'email'      => $order->customer_email ?? '',
                'first_name' => $order->customer_name ?? '',
                'last_name'  => '',
            ],
            'method'      => $method[0],
            'recipient'   => [$method[1] => $normalizedPhone],
            'metadata'    => [
                'type'      => 'refund',
                'order_id'  => $order->id,
                'reference' => 'REFUND-' . $order->reference,
            ],
        ]);
    }

    /**
     * Detecte un pays a partir de l'indicatif telephonique (format E.164).
     */
    public static function detectCountryFromPhone(?string $phone): ?string
    {
        if (empty($phone)) {
            return null;
        }

        $digits = preg_replace('/[^0-9]/', '', $phone);
        if (str_starts_with($digits, '229')) return 'BJ';
        if (str_starts_with($digits, '225')) return 'CI';
        if (str_starts_with($digits, '221')) return 'SN';
        if (str_starts_with($digits, '228')) return 'TG';
        if (str_starts_with($digits, '226')) return 'BF';
        if (str_starts_with($digits, '223')) return 'ML';
        if (str_starts_with($digits, '237')) return 'CM';
        if (str_starts_with($digits, '241')) return 'GA';
        if (str_starts_with($digits, '242')) return 'CG';
        if (str_starts_with($digits, '243')) return 'CD';
        if (str_starts_with($digits, '233')) return 'GH';
        if (str_starts_with($digits, '254')) return 'KE';
        if (str_starts_with($digits, '250')) return 'RW';
        if (str_starts_with($digits, '255')) return 'TZ';
        if (str_starts_with($digits, '256')) return 'UG';
        if (str_starts_with($digits, '234')) return 'NG';
        if (str_starts_with($digits, '227')) return 'NE';
        if (str_starts_with($digits, '224')) return 'GN';

        return null;
    }

    private function apiHeaders(): array
    {
        return [
            'Authorization' => 'Bearer ' . $this->config['secret_key'],
            'Content-Type'  => 'application/json',
            'Accept'        => 'application/json',
        ];
    }
}
