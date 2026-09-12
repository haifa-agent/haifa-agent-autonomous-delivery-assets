@check("functional.couponPropagated")
def coupon_propagated():
    from dto import OrderRequest
    from order_service import create_order

    positional = create_order(OrderRequest("o-2", 5.0, "SAVE10"))
    keyword = create_order(OrderRequest(order_id="o-3", total=7.5, coupon_code="WELCOME"))
    return positional.get("couponCode") == "SAVE10" and keyword.get("couponCode") == "WELCOME"


@check("functional.couponOmittedIsNull")
def coupon_omitted():
    from dto import OrderRequest
    from order_service import create_order

    payload = create_order(OrderRequest("o-1", 10.0))
    return "couponCode" in payload and payload["couponCode"] is None, repr(payload)


@check("functional.replayPreservesCoupon")
def replay_preserves_coupon():
    from order_service import replay

    payload = {"orderId": "o-5", "total": 2.0, "couponCode": "X-1"}
    return replay(payload) == payload, repr(replay(payload))


@check("functional.serializerReadsCoupon")
def serializer_reads_coupon():
    from serializers import from_json

    request = from_json({"orderId": "o-6", "total": 3.0, "couponCode": "SPRING"})
    return getattr(request, "coupon_code", None) == "SPRING"


@check("regression.legacyPayloadReplays")
def legacy_payload():
    from order_service import replay
    from serializers import from_json

    replayed = replay({"orderId": "o-7", "total": 1.5})
    request = from_json({"orderId": "o-8", "total": 4.0})
    return replayed == {"orderId": "o-7", "total": 1.5, "couponCode": None} and request.coupon_code is None, repr(replayed)


@check("regression.wireShape")
def wire_shape():
    from dto import OrderRequest
    from order_service import create_order

    payload = create_order(OrderRequest("o-9", 12.25, "C"))
    return (
        set(payload) == {"orderId", "total", "couponCode"}
        and payload["orderId"] == "o-9"
        and payload["total"] == 12.25
        and isinstance(payload["total"], float)
    ), repr(payload)


@check("regression.positionalConstruction")
def positional_construction():
    import dataclasses

    from dto import OrderRequest

    names = [field.name for field in dataclasses.fields(OrderRequest)]
    request = OrderRequest("o-10", 1.0)
    return names[:2] == ["order_id", "total"] and request.order_id == "o-10" and request.total == 1.0
