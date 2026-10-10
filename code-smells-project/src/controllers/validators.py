"""Validação de entrada reutilizável (T09).

Mesmas mensagens e mesma ordem de verificação do original. Os validadores lançam
ValidationError; o middleware central traduz para a resposta HTTP (T10).
"""
from src.errors import ValidationError

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
NOME_MIN, NOME_MAX = 2, 200


def validar_produto(dados, completo=True):
    if not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")

    # Regras aplicadas só na criação no original.
    if completo:
        if len(nome) < NOME_MIN:
            raise ValidationError("Nome muito curto")
        if len(nome) > NOME_MAX:
            raise ValidationError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def validar_usuario(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    dados = dados or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha


def validar_pedido(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    return usuario_id, itens


def validar_status(dados):
    dados = dados or {}
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status


def parse_preco(valor):
    """Converte parâmetro de preço da query string, com tratamento de erro (T09)."""
    if not valor:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValidationError("Parâmetro de preço inválido")
