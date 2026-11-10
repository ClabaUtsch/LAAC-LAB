"""Validação de CPF brasileiro (somente dígitos)."""


def limpar_cpf(valor: str | None) -> str:
    return "".join(c for c in (valor or "") if c.isdigit())


def cpf_valido(valor: str | None) -> bool:
    digitos = limpar_cpf(valor)
    if len(digitos) != 11:
        return False
    if digitos == digitos[0] * 11:
        return False

    def _dv(base: str, pesos: range) -> str:
        soma = sum(int(n) * p for n, p in zip(base, pesos))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    d1 = _dv(digitos[:9], range(10, 1, -1))
    d2 = _dv(digitos[:9] + d1, range(11, 1, -1))
    return digitos[-2:] == d1 + d2
