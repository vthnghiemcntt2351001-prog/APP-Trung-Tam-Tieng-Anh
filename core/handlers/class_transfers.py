from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from ..models import ClassTransfer
from ..permissions import admin_context, admin_required
from ..services.class_transfers import (
    approve_class_transfer,
    reject_class_transfer,
)


@admin_required
def class_transfer_list(request):
    pending_transfers = (
        ClassTransfer.objects.filter(status=ClassTransfer.Status.PENDING)
        .select_related(
            "student",
            "source_class__course",
            "target_class__course",
            "requested_by",
        )
        .order_by("requested_at")
    )
    processed_transfers = (
        ClassTransfer.objects.exclude(status=ClassTransfer.Status.PENDING)
        .select_related(
            "student",
            "source_class__course",
            "target_class__course",
            "requested_by",
            "approved_by",
        )
        .order_by("-approved_at", "-requested_at")[:50]
    )
    return render(
        request,
        "core/academics/class_transfers/list.html",
        {
            "pending_transfers": pending_transfers,
            "processed_transfers": processed_transfers,
            **admin_context(request),
        },
    )


@admin_required
def class_transfer_approve(request, transfer_id):
    if request.method != "POST":
        return redirect("class_transfer_list")

    try:
        approve_class_transfer(transfer_id=transfer_id, actor=request.user)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, "Đã duyệt và chuyển học viên sang lớp mới.")
    return redirect("class_transfer_list")


@admin_required
def class_transfer_reject(request, transfer_id):
    if request.method != "POST":
        return redirect("class_transfer_list")

    try:
        reject_class_transfer(transfer_id=transfer_id, actor=request.user)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, "Đã từ chối yêu cầu; ghi danh hiện tại không thay đổi.")
    return redirect("class_transfer_list")
