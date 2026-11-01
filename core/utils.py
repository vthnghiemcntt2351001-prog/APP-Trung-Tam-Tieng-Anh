def num_to_vietnamese_words(num):
    """
    Chuyển đổi số tiền thành chữ tiếng Việt chuẩn hóa hóa đơn / phiếu thu tài chính.
    Ví dụ: 4800000 -> "Bốn triệu tám trăm nghìn đồng chẵn."
    """
    units = ['', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín']
    tens = ['', 'mười', 'hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']

    try:
        num = int(num)
    except (ValueError, TypeError):
        return 'Không đồng.'

    if num == 0:
        return 'Không đồng chẵn.'

    def read_three(n):
        res = ''
        h = n // 100
        t = (n % 100) // 10
        u = n % 10
        if h > 0:
            res += units[h] + ' trăm '
        elif res:
            res += 'không trăm '
        if t > 1:
            res += tens[t] + ' '
            if u == 1:
                res += 'mốt '
            elif u == 5:
                res += 'lăm '
            elif u > 0:
                res += units[u] + ' '
        elif t == 1:
            res += 'mười '
            if u == 5:
                res += 'lăm '
            elif u > 0:
                res += units[u] + ' '
        elif t == 0 and u > 0:
            if h > 0:
                res += 'lẻ '
            res += units[u] + ' '
        return res.strip()

    scales = ['', 'nghìn', 'triệu', 'tỷ', 'nghìn tỷ', 'triệu tỷ']
    parts = []
    scale_idx = 0
    temp = abs(num)
    while temp > 0:
        chunk = temp % 1000
        if chunk > 0:
            parts.append(read_three(chunk) + ' ' + scales[scale_idx])
        scale_idx += 1
        temp //= 1000

    result = ' '.join(reversed(parts)).strip()
    result = ' '.join(result.split())
    prefix = 'Âm ' if num < 0 else ''
    return prefix + result.capitalize() + ' đồng chẵn.'
