"""Tests du pré-processeur de messages (app/core/message_interpreter.py).

Vérifie que les entités clés sont extraites à chaque tour, quel que soit
l'agent qui traitera le message — c'est la protection contre
« je suis a calavi » ignoré / « un seul » non compté / « momo » oublié.
"""

from app.core.message_interpreter import (
    apply_to_context,
    interpret_message,
    state_summary,
)
from app.core.schemas import ProductCard
from app.memory.short_term import ConversationContext


class TestCityStopwords:
    """« les deux feront combien » a déjà créé une commande à « feront combien »."""

    def test_feront_combien_is_not_a_city(self):
        ctx = _ctx(product_id="18", product_name="Ordinateur portable HP")
        ext = interpret_message("oui je prend du coup les deux feront combien", ctx)
        apply_to_context(ctx, ext)
        assert ctx.pending_city != "Feront Combien"

    def test_coute_combien_is_not_a_city(self):
        ctx = _ctx(product_id="18", product_name="Ordinateur portable HP")
        ext = interpret_message("sa coute combien au total", ctx)
        apply_to_context(ctx, ext)
        assert ctx.pending_city not in ("Combien Au Total", "Coute Combien")


class TestPhoneExtraction:
    def test_bare_phone_number(self):
        ctx = _ctx()
        ext = interpret_message("0195900616", ctx)
        apply_to_context(ctx, ext)
        assert ctx.user_phone == "0195900616"

    def test_phone_with_marker(self):
        ctx = _ctx()
        ext = interpret_message("mon numéro c'est 0195900616", ctx)
        apply_to_context(ctx, ext)
        assert ctx.user_phone == "0195900616"

    def test_phone_international(self):
        ctx = _ctx()
        ext = interpret_message("+229 01 95 90 06 16", ctx)
        apply_to_context(ctx, ext)
        assert ctx.user_phone == "2290195900616"

    def test_price_is_not_a_phone(self):
        # « je paie 50000000 » → chiffres < 60% du message → pas un téléphone
        ctx = _ctx()
        ext = interpret_message("je paie seulement 50000000 pour tout", ctx)
        apply_to_context(ctx, ext)
        assert ctx.user_phone is None

    def test_small_numbers_ignored(self):
        ctx = _ctx()
        ext = interpret_message("je veux 2", ctx)
        apply_to_context(ctx, ext)
        assert ctx.user_phone is None


class TestConfirmationPerTurn:
    """Un « oui » passé ne doit jamais confirmer une action future."""

    def test_confirmation_resets_each_turn(self):
        ctx = _ctx()
        apply_to_context(ctx, interpret_message("oui", ctx))
        assert ctx.last_user_confirmation == "yes"
        apply_to_context(ctx, interpret_message("les deux feront combien", ctx))
        assert ctx.last_user_confirmation is None


class TestMultiNamedProducts:
    def _cards(self) -> list[ProductCard]:
        return [
            ProductCard(
                id="4", name="iPhone 12 Pro", price="350 000 FCFA",
                raw_price=350000, stock=7, store_id="3",
            ),
            ProductCard(
                id="18", name="Ordinateur portable HP", price="320 000 FCFA",
                raw_price=320000, stock=3, store_id="19",
            ),
        ]

    def test_two_named_products_tracked(self):
        ctx = _ctx(last_cards=self._cards())
        ext = interpret_message("je prend iphone 12 et ordinateur les deux ferons combien", ctx)
        apply_to_context(ctx, ext)
        assert set(ctx.last_named_ids) == {"4", "18"}

    def test_range_suffix_optional(self):
        # « iPhone 12 » matche « iPhone 12 Pro » sans écrire « Pro »
        ctx = _ctx(last_cards=self._cards())
        ext = interpret_message("je veux l'iphone 12", ctx)
        assert "4" in ext.named_product_ids

    def test_unknown_message_clears_last_named_ids(self):
        ctx = _ctx(last_cards=self._cards())
        apply_to_context(ctx, interpret_message("je prend iphone 12", ctx))
        assert ctx.last_named_ids == ["4"]
        apply_to_context(ctx, interpret_message("et combien", ctx))
        assert ctx.last_named_ids == []


def _ctx(**kwargs) -> ConversationContext:
    return ConversationContext(**kwargs)


class TestCityExtraction:
    def test_declared_city_fills_user_city(self):
        ctx = _ctx()
        ext = interpret_message("je suis a calavi", ctx)
        apply_to_context(ctx, ext)
        assert ctx.user_city == "Calavi"

    def test_declared_city_multi_country(self):
        # Pas limité au Bénin : Dakar, Abidjan, Lomé…
        for text, expected in [
            ("je suis a dakar", "Dakar"),
            ("j'habite a abidjan", "Abidjan"),
            ("je suis a lome", "Lome"),
        ]:
            ctx = _ctx()
            ext = interpret_message(text, ctx)
            apply_to_context(ctx, ext)
            assert ctx.user_city == expected

    def test_city_during_order_flow_fills_pending_city(self):
        ctx = _ctx(product_id="42", product_name="Mocassins homme")
        ext = interpret_message("je suis a calavi jai dit", ctx)
        apply_to_context(ctx, ext)
        assert ctx.pending_city == "Calavi"
        assert ctx.user_city == "Calavi"

    def test_city_without_order_context_does_not_fill_pending(self):
        ctx = _ctx()
        ext = interpret_message("je suis a parakou", ctx)
        apply_to_context(ctx, ext)
        assert ctx.pending_city is None


class TestQuantityExtraction:
    def test_un_seul_is_quantity_one(self):
        ctx = _ctx(product_id="42", product_name="Mocassins homme")
        ext = interpret_message("je veux un seul", ctx)
        apply_to_context(ctx, ext)
        assert ctx.pending_quantity == 1

    def test_numeric_quantity(self):
        ctx = _ctx(product_id="42", product_name="Mocassins homme")
        ext = interpret_message("je veux 3", ctx)
        apply_to_context(ctx, ext)
        assert ctx.pending_quantity == 3

    def test_no_quantity_without_order_context(self):
        ctx = _ctx()
        ext = interpret_message("j'ai 2 enfants", ctx)
        apply_to_context(ctx, ext)
        assert ctx.pending_quantity is None


class TestPaymentMethod:
    def test_momo(self):
        ctx = _ctx()
        ext = interpret_message("je prefere momo", ctx)
        apply_to_context(ctx, ext)
        assert ctx.pending_payment_method == "MTN MoMo"

    def test_card(self):
        ctx = _ctx()
        ext = interpret_message("je paie par carte", ctx)
        apply_to_context(ctx, ext)
        assert ctx.pending_payment_method == "carte bancaire"

    def test_wave(self):
        ctx = _ctx()
        ext = interpret_message("je peux payer avec wave", ctx)
        apply_to_context(ctx, ext)
        assert ctx.pending_payment_method == "Wave"


class TestNamedProductSelection:
    def _cards(self) -> list[ProductCard]:
        return [
            ProductCard(
                id="11", name="Mocassins homme", price="22 000 FCFA",
                raw_price=22000, stock=4, store_id="7",
            ),
            ProductCard(
                id="12", name="Baskets running", price="28 000 FCFA",
                raw_price=28000, stock=9, store_id="7",
            ),
        ]

    def test_named_card_becomes_selected_product(self):
        ctx = _ctx(last_cards=self._cards())
        ext = interpret_message("super les mocassins homme je peux les prendre", ctx)
        apply_to_context(ctx, ext)
        assert ctx.product_id == "11"
        assert ctx.product_name == "Mocassins homme"
        assert ctx.product_price == 22000


class TestConfirmation:
    def test_yes(self):
        ctx = _ctx()
        ext = interpret_message("ok", ctx)
        assert ext.confirmation == "yes"

    def test_no(self):
        ctx = _ctx()
        ext = interpret_message("non merci", ctx)
        assert ext.confirmation == "no"


class TestStateSummary:
    def test_summary_includes_all_slots(self):
        ctx = _ctx(
            product_name="Mocassins homme",
            product_price=22000,
            pending_quantity=1,
            pending_city="Calavi",
            pending_payment_method="MTN MoMo",
        )
        summary = state_summary(ctx)
        assert "Mocassins homme" in summary
        assert "quantité=1" in summary
        assert "Calavi" in summary
        assert "MTN MoMo" in summary

    def test_empty_context_empty_summary(self):
        assert state_summary(_ctx()) == ""
