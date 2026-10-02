import pytest

from robotops.domain.models import OrderLine, OrderRequest


@pytest.fixture
def order_request():
    return OrderRequest(
        order_id="order-1",
        lines=(
            OrderLine(
                order_line_id="line-1",
                product_id="product-red",
                source_id="source",
                destination_id="destination",
            ),
        ),
    )
