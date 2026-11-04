"""Validação de entrada. Mensagens e ordem de verificação são as do código original;
as checagens de tipo novas só recusam entradas que antes davam 500 ou corrompiam dados."""
from src.errors import ValidationError
from src.services.pedido_service import STATUS_VALIDOS

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_MIN = 2
NOME_MAX = 200
MAX_PAGE_SIZE = 100

OBRIGATORIOS_PRODUTO = (
    ("nome", "Nome é obrigatório"),
    ("preco", "Preço é obrigatório"),
    ("estoque", "Estoque é obrigatório"),
)


def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _inteiro(valor):
    """Converte ids e quantidades aceitos pelo original (1, "1", 1.0); None se não der."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    if isinstance(valor, str):
        try:
            return int(valor.strip())
        except ValueError:
            return None
    return None


def validar_produto(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    for campo, mensagem in OBRIGATORIOS_PRODUTO:
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not _eh_numero(preco):
        raise ValidationError("Preço inválido")
    if not _eh_numero(estoque):
        raise ValidationError("Estoque inválido")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def validar_usuario(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    campos = (dados.get("nome", ""), dados.get("email", ""), dados.get("senha", ""))
    if not all(campos) or not all(isinstance(campo, str) for campo in campos):
        raise ValidationError("Nome, email e senha são obrigatórios")
    return campos


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha or not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha


def validar_pedido(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    usuario_id = _inteiro(usuario_id)
    if usuario_id is None:
        raise ValidationError("Usuario ID inválido")
    if not isinstance(itens, list):
        raise ValidationError("Itens do pedido inválidos")

    itens_validos = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item do pedido inválido")
        produto_id = _inteiro(item.get("produto_id"))
        quantidade = _inteiro(item.get("quantidade"))
        if produto_id is None:
            raise ValidationError("Item do pedido inválido")
        # Quantidade negativa somava estoque no original (estoque - -N).
        if quantidade is None or quantidade < 1:
            raise ValidationError("Quantidade inválida")
        itens_validos.append({"produto_id": produto_id, "quantidade": quantidade})
    return usuario_id, itens_validos


def validar_status(dados):
    dados = dados if isinstance(dados, dict) else {}
    status = dados.get("status", "")
    if not isinstance(status, str) or status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return status


def _preco_filtro(args, nome):
    valor = args.get(nome, None)
    # Mesma truthiness do original: parâmetro vazio é ignorado.
    if not valor:
        return valor
    try:
        return float(valor)
    except ValueError:
        raise ValidationError("Parâmetro " + nome + " inválido")


def validar_filtros_busca(args):
    return (
        args.get("q", ""),
        args.get("categoria", None),
        _preco_filtro(args, "preco_min"),
        _preco_filtro(args, "preco_max"),
    )


def validar_paginacao(args):
    """Paginação opcional: sem `limit`, a listagem é completa, como no original."""
    if "limit" not in args:
        return None, 0
    try:
        limit = min(int(args["limit"]), MAX_PAGE_SIZE)
        offset = int(args.get("offset", 0))
    except ValueError:
        raise ValidationError("Parâmetros de paginação inválidos")
    if limit < 0 or offset < 0:
        raise ValidationError("Parâmetros de paginação inválidos")
    return limit, offset
