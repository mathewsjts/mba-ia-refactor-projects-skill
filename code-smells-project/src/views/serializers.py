"""Representação pública das entidades. Campos fora destas listas (ex.: senha) não saem na API."""

CAMPOS_PRODUTO = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")
CAMPOS_USUARIO = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_USUARIO_LOGIN = ("id", "nome", "email", "tipo")
CAMPOS_PEDIDO = ("id", "usuario_id", "status", "total", "criado_em")
CAMPOS_ITEM_PEDIDO = ("produto_id", "produto_nome", "quantidade", "preco_unitario")


def _campos(entidade, campos):
    return {campo: entidade[campo] for campo in campos}


def serialize_produto(produto):
    return _campos(produto, CAMPOS_PRODUTO)


def serialize_produtos(produtos):
    return [serialize_produto(produto) for produto in produtos]


def serialize_usuario(usuario):
    return _campos(usuario, CAMPOS_USUARIO)


def serialize_usuarios(usuarios):
    return [serialize_usuario(usuario) for usuario in usuarios]


def serialize_login(usuario, token):
    return {**_campos(usuario, CAMPOS_USUARIO_LOGIN), "token": token}


def serialize_pedido(pedido):
    return {
        **_campos(pedido, CAMPOS_PEDIDO),
        "itens": [_campos(item, CAMPOS_ITEM_PEDIDO) for item in pedido["itens"]],
    }


def serialize_pedidos(pedidos):
    return [serialize_pedido(pedido) for pedido in pedidos]
