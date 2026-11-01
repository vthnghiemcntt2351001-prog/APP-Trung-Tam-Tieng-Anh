from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Bảo toàn toàn bộ GET parameters hiện tại (tìm kiếm, lọc, sắp xếp)
    và ghi đè/thay thế các tham số truyền vào (ví dụ: page=2).

    Sử dụng trong template:
        <a href="?{% query_transform page=page_num %}">{{ page_num }}</a>
    """
    request = context.get("request")
    if not request:
        return ""

    query_params = request.GET.copy()
    for key, value in kwargs.items():
        if value is not None and value != "":
            query_params[key] = value
        elif key in query_params:
            del query_params[key]

    return query_params.urlencode()


@register.filter
def get_elided_pages(page_obj, on_each_side=2, on_ends=1):
    """
    Trả về danh sách các số trang có rút gọn dấu '...' (Ellipsis)
    ví dụ: [1, 2, '...', 9, 10, 11, '...', 45]
    """
    if not page_obj or not hasattr(page_obj, "paginator"):
        return []
    paginator = page_obj.paginator
    return paginator.get_elided_page_range(
        number=page_obj.number,
        on_each_side=on_each_side,
        on_ends=on_ends
    )


@register.filter
def currency_vnd(value):
    """
    Format số tiền theo chuẩn VNĐ có dấu phân cách hàng nghìn:
    Ví dụ: 3900000 -> 3.900.000 ₫
    """
    if value is None or value == "":
        return "0 ₫"
    try:
        val = int(round(float(value)))
        return f"{val:,}".replace(",", ".") + " ₫"
    except (ValueError, TypeError):
        return f"{value} ₫"

