"""Validação de entrada reutilizável (T09).

Mantém as mesmas mensagens e a mesma ordem de verificação do original; as regras
de criação e atualização de produto diferem, como no código legado.
"""
from src.errors import ValidationError

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
NOME_MIN = 2
NOME_MAX = 200
MAX_PAGE_SIZE = 100


def parse_paginacao(args):
    """Paginação opt-in (T17): sem `limit`, devolve (None, 0) e a listagem é completa."""
    if "limit" not in args:
        return None, 0
    try:
        limit = min(int(args["limit"]), MAX_PAGE_SIZE)
        offset = int(args.get("offset", 0))
    except (ValueError, TypeError):
        raise ValidationError("Parâmetros de paginação inválidos")
    return limit, offset

_OBRIGATORIOS_PRODUTO = (
    ("nome", "Nome é obrigatório"),
    ("preco", "Preço é obrigatório"),
    ("estoque", "Estoque é obrigatório"),
)


def validar_produto(dados, completo=True):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo, mensagem in _OBRIGATORIOS_PRODUTO:
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")

    if completo:
        if len(nome) < NOME_MIN:
            raise ValidationError("Nome muito curto")
        if len(nome) > NOME_MAX:
            raise ValidationError("Nome muito longo")
        categoria = dados.get("categoria", "geral")
        if categoria not in CATEGORIAS_VALIDAS:
            raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {
        "nome": nome,
        "descricao": dados.get("descricao", ""),
        "preco": preco,
        "estoque": estoque,
        "categoria": dados.get("categoria", "geral"),
    }


def validar_usuario(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    return nome, email, senha


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
