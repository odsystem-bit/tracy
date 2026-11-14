<?php

declare(strict_types=1);

namespace App\Services\Payment;

/**
 * @deprecated Utilisez PaymentService directement.
 */
class MonerooService
{
    /**
     * Crée un lien de paiement via PaymentService unifié.
     *
     * @param array $data
     * @return array
     * @throws \Exception
     */
    public static function createPaymentLink(array $data): array
    {
        $service = app(PaymentService::class);

        $result = $service->initializePayment([
            'amount'      => $data['amount'],
            'description' => $data['description'] ?? ('Paiement ' . ($data['reference'] ?? '')),
            'customer'    => [
                'first_name' => $data['customer_name'] ?? '',
                'email'      => $data['customer_email'] ?? '',
                'phone'      => $data['customer_phone'] ?? '',
            ],
            'return_url'  => $data['return_url'] ?? '',
            'metadata'    => [
                'reference' => $data['reference'] ?? '',
            ],
        ]);

        if (! $result['success']) {
            throw new \Exception($result['message'] ?? 'Erreur création lien paiement Moneroo');
        }

        return ['url' => $result['checkout_url']];
    }
}
