"""Serializers com whitelist de campos públicos (T13).

Nenhum serializer expõe `senha` (BC-04). A representação de login não traz
`criado_em`, mantendo exatamente o contrato original.
"""


def serialize_produto(produto):
    return {
        "id": produto["id"],
        "nome": produto["nome"],
        "descricao": produto["descricao"],
        "preco": produto["preco"],
        "estoque": produto["estoque"],
        "categoria": produto["categoria"],
        "ativo": produto["ativo"],
        "criado_em": produto["criado_em"],
    }


def serialize_produtos(produtos):
    return [serialize_produto(p) for p in produtos]


def serialize_usuario(usuario):
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
        "criado_em": usuario["criado_em"],
    }


def serialize_usuarios(usuarios):
    return [serialize_usuario(u) for u in usuarios]


def serialize_login(usuario):
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
    }


def serialize_item_pedido(item):
    return {
        "produto_id": item["produto_id"],
        "produto_nome": item["produto_nome"],
        "quantidade": item["quantidade"],
        "preco_unitario": item["preco_unitario"],
    }


def serialize_pedido(pedido):
    return {
        "id": pedido["id"],
        "usuario_id": pedido["usuario_id"],
        "status": pedido["status"],
        "total": pedido["total"],
        "criado_em": pedido["criado_em"],
        "itens": [serialize_item_pedido(i) for i in pedido["itens"]],
    }


def serialize_pedidos(pedidos):
    return [serialize_pedido(p) for p in pedidos]
