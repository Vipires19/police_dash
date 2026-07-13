"""Testes unitários do algoritmo de distribuição DEJEM (função pura)."""

from __future__ import annotations

import unittest

from services.dejem_distribution_service import (
    DistributionCandidate,
    compute_distribution,
)


def _c(
    user_id: int,
    desired: int,
    *,
    patente_rank: int = 7,
    display_order: int | None = None,
    nome: str | None = None,
) -> DistributionCandidate:
    return DistributionCandidate(
        user_id=user_id,
        desired_slots=desired,
        patente_rank=patente_rank,
        display_order=display_order if display_order is not None else user_id,
        nome_guerra=nome or f"P{user_id:02d}",
    )


class TestDejemDistribution(unittest.TestCase):
    def test_distribuicao_exata(self) -> None:
        """100 vagas / 20 policiais → 5 para todos."""
        candidates = [_c(i, desired=10, display_order=i) for i in range(20)]
        result = compute_distribution(100, 10, candidates)
        self.assertEqual(result.base_quantity, 5)
        self.assertEqual(result.remaining_after_base, 0)
        self.assertEqual(result.leftover_slots, 0)
        self.assertEqual(len(result.allocations), 20)
        self.assertTrue(all(v == 5 for v in result.allocations.values()))

    def test_sobra_de_vagas(self) -> None:
        """97 vagas / 20 → base 4; 17 mais antigos recebem +1."""
        candidates = [_c(i, desired=10, display_order=i) for i in range(20)]
        result = compute_distribution(97, 10, candidates)
        self.assertEqual(result.base_quantity, 4)
        self.assertEqual(result.remaining_after_base, 17)
        self.assertEqual(sum(result.allocations.values()), 97)
        fives = [uid for uid, v in result.allocations.items() if v == 5]
        fours = [uid for uid, v in result.allocations.items() if v == 4]
        self.assertEqual(len(fives), 17)
        self.assertEqual(len(fours), 3)
        # Mais antigos (menor display_order) recebem o +1.
        self.assertEqual(sorted(fives), list(range(17)))
        self.assertEqual(sorted(fours), [17, 18, 19])

    def test_policial_deseja_menos(self) -> None:
        """João deseja 2; recebe 2; sobras voltam à redistribuição."""
        candidates = [_c(i, desired=10, display_order=i) for i in range(20)]
        candidates[5] = _c(5, desired=2, display_order=5, nome="Joao")
        result = compute_distribution(97, 10, candidates)
        self.assertEqual(result.allocations[5], 2)
        self.assertEqual(sum(result.allocations.values()), 97)
        # Ninguém ultrapassa o desejo.
        for c in candidates:
            self.assertLessEqual(result.allocations[c.user_id], c.desired_slots)

    def test_policial_deseja_mais(self) -> None:
        """Carlos deseja 10 e pode receber até o limite nas rodadas extras."""
        candidates = [_c(i, desired=4, display_order=i) for i in range(19)]
        candidates.append(_c(19, desired=10, display_order=0, patente_rank=0, nome="Carlos"))
        # Carlos é o mais antigo (patente_rank 0). Demais saturam na base (desejo 4).
        result = compute_distribution(97, 10, candidates)
        self.assertEqual(result.allocations[19], 10)
        self.assertEqual(sum(result.allocations.values()), 19 * 4 + 10)
        self.assertEqual(result.leftover_slots, 97 - 86)

    def test_limite_mensal(self) -> None:
        """Ninguém ultrapassa o limite mensal mesmo desejando mais."""
        candidates = [_c(i, desired=20, display_order=i) for i in range(5)]
        result = compute_distribution(100, 3, candidates)
        self.assertTrue(all(v <= 3 for v in result.allocations.values()))
        self.assertEqual(sum(result.allocations.values()), 15)
        self.assertEqual(result.leftover_slots, 85)

    def test_nenhum_interessado(self) -> None:
        result = compute_distribution(97, 10, [])
        self.assertEqual(result.allocations, {})
        self.assertEqual(result.base_quantity, 0)
        self.assertEqual(result.leftover_slots, 97)

    def test_apenas_um_interessado(self) -> None:
        result = compute_distribution(97, 10, [_c(1, desired=10, display_order=0)])
        self.assertEqual(result.allocations, {1: 10})
        self.assertEqual(result.leftover_slots, 87)

    def test_vagas_insuficientes(self) -> None:
        """3 vagas / 20 interessados → 3 mais antigos recebem 1."""
        candidates = [_c(i, desired=10, display_order=i) for i in range(20)]
        result = compute_distribution(3, 10, candidates)
        self.assertEqual(result.base_quantity, 0)
        self.assertEqual(sum(result.allocations.values()), 3)
        receivers = [uid for uid, v in result.allocations.items() if v == 1]
        self.assertEqual(sorted(receivers), [0, 1, 2])

    def test_vagas_maiores_que_capacidade(self) -> None:
        """Mais vagas do que a soma dos desejos → leftover."""
        candidates = [_c(i, desired=2, display_order=i) for i in range(5)]
        result = compute_distribution(100, 10, candidates)
        self.assertEqual(sum(result.allocations.values()), 10)
        self.assertEqual(result.leftover_slots, 90)
        self.assertTrue(all(v == 2 for v in result.allocations.values()))

    def test_reproduzivel(self) -> None:
        candidates = [
            _c(i, desired=7 if i % 3 else 3, display_order=i % 7, patente_rank=i % 4)
            for i in range(25)
        ]
        a = compute_distribution(97, 10, candidates)
        b = compute_distribution(97, 10, list(reversed(candidates)))
        self.assertEqual(a.allocations, b.allocations)
        self.assertEqual(a.base_quantity, b.base_quantity)
        self.assertEqual(a.remaining_after_base, b.remaining_after_base)
        self.assertEqual(a.leftover_slots, b.leftover_slots)

    def test_antiguidade_por_patente(self) -> None:
        """Patente mais alta (rank menor) recebe sobra antes."""
        candidates = [
            _c(1, desired=10, patente_rank=7, display_order=0, nome="Soldado"),
            _c(2, desired=10, patente_rank=0, display_order=99, nome="Tenente"),
        ]
        result = compute_distribution(3, 10, candidates)
        self.assertEqual(result.allocations[2], 2)  # tenente mais antigo
        self.assertEqual(result.allocations[1], 1)


if __name__ == "__main__":
    unittest.main()
