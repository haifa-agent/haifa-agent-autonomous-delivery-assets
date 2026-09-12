OLD = ("NEW", "PAID", "SHIPPED", "FINISHED")
OLD_ALLOWED = {("NEW", "PAID"), ("PAID", "SHIPPED"), ("SHIPPED", "FINISHED")}


@check("functional.cancelledValue")
def cancelled_value():
    from models import OrderStatus

    return OrderStatus("CANCELLED").value == "CANCELLED" and OrderStatus.CANCELLED == "CANCELLED"


@check("functional.cancellableStates")
def cancellable():
    from models import OrderStatus
    from state_machine import can_transition

    cancelled = OrderStatus("CANCELLED")
    return can_transition(OrderStatus.NEW, cancelled) is True and can_transition(OrderStatus.PAID, cancelled) is True


@check("boundary.lateStatesCannotCancel")
def late_states():
    from models import OrderStatus
    from state_machine import can_transition

    cancelled = OrderStatus("CANCELLED")
    return not can_transition(OrderStatus.SHIPPED, cancelled) and not can_transition(OrderStatus.FINISHED, cancelled)


@check("boundary.cancelledIsTerminal")
def terminal():
    from models import OrderStatus
    from state_machine import can_transition

    cancelled = OrderStatus("CANCELLED")
    return not any(can_transition(cancelled, target) for target in OrderStatus)


@check("functional.cancelledRendering")
def rendering():
    from models import OrderStatus
    from views import render

    return render(OrderStatus("CANCELLED")) == "Cancelled"


@check("regression.existingTransitionMatrix")
def existing_matrix():
    from models import OrderStatus
    from state_machine import can_transition
    from views import render

    for current in OLD:
        for target in OLD:
            expected = (current, target) in OLD_ALLOWED
            if bool(can_transition(OrderStatus(current), OrderStatus(target))) != expected:
                return False, f"{current} -> {target} changed"
    labels = [render(OrderStatus(value)) for value in OLD]
    return labels == ["New order", "Paid", "Shipped", "Finished"], f"labels {labels}"


@check("regression.statusCounts")
def status_counts_check():
    from models import OrderStatus
    from reports import status_counts

    counts = status_counts([OrderStatus.NEW, OrderStatus("CANCELLED"), OrderStatus("CANCELLED")])
    return counts == {"NEW": 1, "PAID": 0, "SHIPPED": 0, "FINISHED": 0, "CANCELLED": 2}, repr(counts)
